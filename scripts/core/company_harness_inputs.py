"""Shared deterministic limits for the host's immutable worker input package."""
import base64
import hashlib
import json
import mimetypes

from company_harness import HarnessError
from company_harness_contract import MAX_INPUTS, MAX_BYTES

def _cycle_provenance(store):
    try:
        snapshot = store.snapshot()
        cycles = snapshot.get('cycles', []) if isinstance(snapshot, dict) else []
    except Exception:
        return {}, {}
    by_cycle = {}
    heads = {}
    for cycle in cycles:
        by_cycle[cycle['cycleId']] = cycle
        if cycle.get('protocolState') != 'closed' or cycle.get('outcome') != 'completed':
            continue
        ak = (cycle.get('contract') or {}).get('artifactKind')
        if not ak or ak == 'review':
            continue
        sub_id = ((cycle.get('closeReceipt') or {}).get('input') or {}).get('submissionId')
        sub = next((s for s in cycle.get('submissions', []) if s['submissionId'] == sub_id), None) if sub_id else (cycle.get('submissions') or [None])[-1]
        if not sub:
            continue
        payload = sub.get('payload') or {}
        if payload.get('result') != 'completed':
            continue
        refs = payload.get('evidenceRefs', [])
        pid = payload.get('primaryEvidenceId')
        match = next((r for r in refs if r.get('evidenceId') == pid), None) if pid else (refs[0] if len(refs) == 1 else None)
        if match and isinstance(match.get('evidenceId'), str) and isinstance(match.get('sha256'), str):
            scope = (cycle.get('productId') or '', cycle.get('explorationId') or '', ak)
            heads[scope] = (match['evidenceId'], match['sha256'])
    return by_cycle, set(heads.values())


def load_inputs(store, contract):
    references = {}
    for field in ('inputRefs', 'prerequisiteRefs'):
        refs = contract.get(field, [])
        if not isinstance(refs, list):
            raise HarnessError('INPUT_PACKAGE_INVALID', field)
        for ref in refs:
            if (not isinstance(ref, dict) or not isinstance(ref.get('evidenceId'), str) or not ref['evidenceId']
                    or not isinstance(ref.get('sha256'), str) or len(ref['sha256']) != 64):
                raise HarnessError('INPUT_PACKAGE_INVALID', field)
            previous = references.get(ref['evidenceId'])
            if previous is not None and previous != ref['sha256']:
                raise HarnessError('INPUT_PACKAGE_INVALID', field)
            references[ref['evidenceId']] = ref['sha256']
            if len(references) > MAX_INPUTS:
                raise HarnessError('INPUT_PACKAGE_INVALID', 'inputRefs')
    by_cycle, head_pairs = _cycle_provenance(store) if references else ({}, set())
    result, total = [], 0
    for identity, digest in references.items():
        evidence = store.read_evidence(identity)
        if not evidence or evidence.get('sha256') != digest:
            raise HarnessError('EVIDENCE_MISSING', 'inputRefs')
        try:
            content, encoding = evidence['content'], evidence.get('contentEncoding')
            if not isinstance(content, str) or encoding not in {None, 'base64'}:
                raise ValueError()
            data = base64.b64decode(content, validate=True) if encoding == 'base64' else content.encode('utf-8')
            media_type = evidence['mediaType']
            if not isinstance(media_type, str) or not media_type:
                raise ValueError()
        except (KeyError, ValueError, TypeError, UnicodeError) as error:
            raise HarnessError('INPUT_PACKAGE_INVALID', 'inputRefs') from error
        total += len(data)
        if total > MAX_BYTES or hashlib.sha256(data).hexdigest() != digest:
            raise HarnessError('INPUT_PACKAGE_INVALID', 'inputRefs')
        owner = by_cycle.get(evidence.get('cycleId'))
        item = {'evidenceId': identity, 'sha256': digest, 'mediaType': media_type, 'data': data}
        if owner:
            item.update({
                'sourceCycleId': owner.get('cycleId'),
                'sourceWorkKind': owner.get('workKind'),
                'sourceArtifactKind': (owner.get('contract') or {}).get('artifactKind'),
                'sourceOutcome': owner.get('outcome'),
                'isCompletedHead': (identity, digest) in head_pairs,
            })
        result.append(item)
    return result


def write_inputs(materials, directory):
    directory.mkdir()
    index = []
    for material in materials:
        extension = mimetypes.guess_extension(material['mediaType']) or '.bin'
        name = str(len(index)) + '-' + material['sha256'] + extension
        (directory / name).write_bytes(material['data'])
        entry = {key: material[key] for key in ('evidenceId', 'sha256', 'mediaType')}
        entry['file'] = name
        for meta_key in ('sourceCycleId', 'sourceWorkKind', 'sourceArtifactKind', 'sourceOutcome', 'isCompletedHead'):
            if meta_key in material:
                entry[meta_key] = material[meta_key]
        index.append(entry)
    (directory / 'index.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
