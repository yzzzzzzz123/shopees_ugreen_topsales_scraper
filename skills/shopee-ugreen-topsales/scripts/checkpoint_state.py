"""OOXML custom XML recovery state; the four visible sheets stay unchanged."""
from io import BytesIO
import hashlib
import json
import zipfile
from xml.etree import ElementTree as ET

PART = 'customXml/ugreenCapture.xml'
NS = 'urn:ugreen:checkpoint:1'
RELS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CONTENT = 'http://schemas.openxmlformats.org/package/2006/content-types'
REL_TYPE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml'

def encode(payload, origin):
    body=json.dumps(dict(payload=payload,origin=origin),ensure_ascii=False,allow_nan=False,separators=(',',':'))
    root=ET.Element('{'+NS+'}checkpoint',version='1',sha256=hashlib.sha256(body.encode()).hexdigest())
    root.text=body
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def read_embedded(path):
    with zipfile.ZipFile(path) as source:
        names=source.namelist()
        if len(names)!=len(set(names)):
            raise ValueError('进度工作簿含重复 ZIP 部件')
        if PART not in names: return None
        if source.getinfo(PART).file_size>32*1024*1024:
            raise ValueError('恢复状态超出大小上限')
        data=source.read(PART)
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('恢复状态不允许 XML 实体')
    root=ET.fromstring(data)
    if root.tag!='{'+NS+'}checkpoint' or root.get('version')!='1' or len(root):
        raise ValueError('恢复状态版本或结构不受支持')
    body=root.text or ''
    if hashlib.sha256(body.encode()).hexdigest()!=root.get('sha256'):
        raise ValueError('恢复状态校验值不一致')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('恢复状态重复 JSON 字段')
            result[key]=value
        return result
    def invalid(value): raise ValueError('恢复状态含非有限数值：'+value)
    state=json.loads(body,object_pairs_hook=unique,parse_constant=invalid)
    if type(state) is not dict or set(state)!={'payload','origin'} or type(state['origin']) is not dict:
        raise ValueError('恢复状态字段不符')
    return state

def embed_state(path, payload, origin=None):
    changes={PART:encode(payload,origin or {'kind':'native_capture'})}
    with zipfile.ZipFile(path) as source:
        names=source.namelist()
        if len(names)!=len(set(names)): raise ValueError('重复 ZIP 部件')
        rels=ET.fromstring(source.read('_rels/.rels'))
        for node in list(rels):
            if node.get('Target')==PART:
                rels.remove(node)
            elif node.get('Id')=='ugreenCaptureState':
                raise ValueError('恢复状态关系 ID 冲突')
        ET.SubElement(rels,'{'+RELS+'}Relationship',Id='ugreenCaptureState',Type=REL_TYPE,Target=PART)
        changes['_rels/.rels']=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
        types=ET.fromstring(source.read('[Content_Types].xml'))
        for node in list(types):
            if node.get('PartName')=='/'+PART: types.remove(node)
        ET.SubElement(types,'{'+CONTENT+'}Override',PartName='/'+PART,ContentType='application/xml')
        changes['[Content_Types].xml']=ET.tostring(types,encoding='utf-8',xml_declaration=True)
        out=BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as target:
            for entry in source.infolist():
                target.writestr(entry,changes.pop(entry.filename,source.read(entry.filename)))
            for name,data in changes.items(): target.writestr(name,data)
    path.write_bytes(out.getvalue())
