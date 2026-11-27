"""Shared deterministic limits for the host's immutable worker input package."""
import base64
import hashlib
import json
import mimetypes

from company_harness import HarnessError
from company_harness_contract import MAX_INPUTS, MAX_BYTES

def _cycle_provenance(store, contract=None):
    try:
        snapshot = store.snapshot()
        cycles = snapshot.get('cycles', []) if isinstance(snapshot, dict) else []
    except Exception:
        return {}, None
    by_cycle = {cycle['cycleId']: cycle for cycle in cycles}
    from company_harness_quality import artifact_state
    contract = contract or {}
    if contract.get('productId') or contract.get('explorationId'):
        scope = {
            'productId': contract.get('productId'),
            'explorationId': contract.get('explorationId'),
        }
        heads = artifact_state(store, scope)['heads']
        return by_cycle, {(h['evidenceId'], h['sha256']) for h in heads.values()}
    return by_cycle, None


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
    by_cycle, head_pairs = _cycle_provenance(store, contract) if references else ({}, set())
    scoped_head_cache = {}
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
            effective_heads = head_pairs
            if effective_heads is None:
                from company_harness_quality import artifact_state
                owner_key = (owner.get('productId'), owner.get('explorationId'))
                if owner_key not in scoped_head_cache:
                    heads = artifact_state(store, {'productId': owner_key[0], 'explorationId': owner_key[1]})['heads']
                    scoped_head_cache[owner_key] = {(h['evidenceId'], h['sha256']) for h in heads.values()}
                effective_heads = scoped_head_cache[owner_key]
            item.update({
                'sourceCycleId': owner.get('cycleId'),
                'sourceWorkKind': owner.get('workKind'),
                'sourceArtifactKind': (owner.get('contract') or {}).get('artifactKind'),
                'sourceOutcome': owner.get('outcome'),
                'isCompletedHead': (identity, digest) in effective_heads,
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
