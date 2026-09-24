"""在隔离 Git 仓库验证日期分支归档、同日版本保留和按观察时间回看。"""
from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parents[1]/'skills/shopee-ugreen-topsales/scripts'
sys.path.insert(0,str(SCRIPTS))
import analysis_report as report
import excel
import publish_result as publisher
import snapshot_history as history
from test_publish_result import fixture,template


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';self.root.mkdir()
        self.daily=self.root/'worktrees/20000102_ugreen_topsales'
        spec=self.root/publisher.TEMPLATE_RELATIVE;spec.parent.mkdir(parents=True);template(spec)
        script=self.root/publisher.SCRIPT_RELATIVE;script.parent.mkdir(parents=True);shutil.copyfile(SCRIPTS/'publish_result.py',script)
        (self.root/'.gitignore').write_text('/result/*\n/worktrees/\n')
        self.git(self.root,'init','-b','main');self.git(self.root,'config','user.name','Offline Fixture');self.git(self.root,'config','user.email','offline@example.invalid')
        self.git(self.root,'add','.');self.git(self.root,'commit','-m','隔离测试初始源码')
        self.git(self.root,'worktree','add','-b','daily/20000102-ugreen-topsales',str(self.daily))
        patcher=patch.object(publisher,'__file__',str(self.daily/publisher.SCRIPT_RELATIVE));patcher.start();self.addCleanup(patcher.stop)
        publisher.publish(fixture(),self.root,self.daily)
        report.write_report(self.root,self.daily)

    def git(self,path,*args):
        return subprocess.run(['git',*args],cwd=path,check=True,capture_output=True,text=True).stdout.strip()

    def test_pair_is_committed_and_unrelated_staged_work_is_preserved(self):
        note=self.daily/'notes.txt';note.write_text('user changes')
        self.git(self.daily,'add','notes.txt')
        receipt=history.archive_result(self.root,self.daily)
        self.assertEqual(receipt['archive_status'],'通过');self.assertTrue(receipt['created'])
        self.assertEqual(self.git(self.daily,'diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines(),[history.WORKBOOK,history.REPORT])
        self.assertEqual(self.git(self.daily,'diff','--cached','--name-only'),'notes.txt')
        self.assertEqual(history.read_blob(self.daily,receipt['commit']), (self.daily/history.WORKBOOK).read_bytes())
        second=history.archive_result(self.root,self.daily)
        self.assertFalse(second['created']);self.assertEqual(second['commit'],receipt['commit'])

    def test_republish_preserves_old_pair_then_new_pair_and_can_read_deleted_workbook(self):
        old_bytes=(self.daily/history.WORKBOOK).read_bytes()
        updated=fixture();updated['captured_at']='2000-01-03T01:01:00+08:00';updated['pages'][0]['cards'][0]['price_php']=21
        publisher.publish(updated,self.root,self.daily)
        commits=history.revisions(self.daily);self.assertEqual(len(commits),1)
        self.assertEqual(history.read_blob(self.daily,commits[0]),old_bytes)
        report.write_report(self.root,self.daily);receipt=history.archive_result(self.root,self.daily)
        self.assertEqual(len(history.revisions(self.daily)),2)
        back=history.latest_snapshot(self.root,self.daily,'2000/01/03 00:30:00')
        self.assertEqual(back.sha256,hashlib.sha256(old_bytes).hexdigest());self.assertEqual(back.revision,commits[0])
        output=self.daily/history.WORKBOOK;output.unlink()
        restored=history.latest_snapshot(self.root,self.daily,'2000/01/03 02:00:00')
        self.assertEqual(restored.revision,receipt['commit']);self.assertFalse(output.exists())

    def test_mismatched_pdf_never_creates_history_commit(self):
        before=self.git(self.daily,'rev-parse','HEAD')
        target=self.daily/history.REPORT;target.write_bytes(target.read_bytes()+b'edit')
        with self.assertRaisesRegex(ValueError,'不一致'):history.archive_result(self.root,self.daily)
        self.assertEqual(self.git(self.daily,'rev-parse','HEAD'),before)


if __name__=='__main__':unittest.main()
