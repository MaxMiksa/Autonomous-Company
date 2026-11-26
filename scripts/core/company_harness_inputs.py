"""Shared deterministic limits for the host's immutable worker input package."""
import base64
import hashlib
import json
import mimetypes

from company_harness import HarnessError
from company_harness_contract import MAX_INPUTS, MAX_BYTES

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
        result.append({'evidenceId': identity, 'sha256': digest, 'mediaType': media_type, 'data': data})
    return result


def write_inputs(materials, directory):
    directory.mkdir()
    index = []
    for material in materials:
        extension = mimetypes.guess_extension(material['mediaType']) or '.bin'
        name = str(len(index)) + '-' + material['sha256'] + extension
        (directory / name).write_bytes(material['data'])
        index.append({**{key: material[key] for key in ('evidenceId', 'sha256', 'mediaType')}, 'file': name})
    (directory / 'index.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
