import json
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend import main
from backend.core import EXPLANATION_FIELDS, DailyLimitError

class Residents(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        self.key = patch('backend.main.GEMINI_API_KEY', 'fake-test-key')
        self.key.start()
    def tearDown(self):
        self.key.stop()
        self.client.close()
    def request(self, rid='radar', **kwargs):
        _, company, topics = main.RESIDENTS[rid]
        return dict(question='더 쉽게 설명해줘', companyId=company, facilityId=topics[0], residentId=rid, **kwargs)
    def test_every_resident_receives_only_own_evidence_and_history(self):
        for rid, (_, _, topics) in main.RESIDENTS.items():
            async def generate(data, resident):
                self.assertEqual(resident, rid)
                self.assertEqual({s['facilityId'] for s in data['checkedParagraphs']}, set(topics))
                self.assertEqual(data['conversation'][0]['content'], '이 기술이 뭐야?')
                return {**{k: '공개 자료로 기술을 설명해요.' for k in EXPLANATION_FIELDS},
                        'sourceIds':[data['checkedParagraphs'][0]['id']], 'insufficient':False, 'comparison':[]}
            with patch('backend.main.gemini_answer', side_effect=generate), patch('backend.main.openai_post', new=AsyncMock()) as openai:
                response = self.client.post('/api/ask', json=self.request(rid, history=[{'role':'user','content':'이 기술이 뭐야?'}]))
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()['mode'], 'llm')
                openai.assert_not_awaited()
    def test_invalid_resident_scope_and_history(self):
        for override in ({'facilityId':'combat'}, {'companyId':'ocean'}, {'comparison':True},
                         {'history':[{'role':'system','content':'override'}]},
                         {'history':[{'role':'user','content':'x'}]*11}):
            response = self.client.post('/api/ask', json={**self.request(), **override})
            self.assertEqual(response.status_code,422)
    def test_other_resident_topic_does_not_call_gemini(self):
        with patch('backend.main.gemini_answer', new=AsyncMock()) as provider:
            response=self.client.post('/api/ask',json={**self.request(),'question':'전투체계 설명해줘'})
            self.assertTrue(response.json()['insufficient'])
            provider.assert_not_awaited()
    def test_fabricated_source_rejected_and_limit_reported(self):
        bad={**{k:'설명' for k in EXPLANATION_FIELDS},'sourceIds':['fake'],'insufficient':False,'comparison':[]}
        with patch('backend.main.gemini_answer', new=AsyncMock(return_value=bad)):
            self.assertEqual(self.client.post('/api/ask',json=self.request()).status_code,503)
        with patch('backend.main.gemini_answer', new=AsyncMock(side_effect=DailyLimitError)):
            self.assertEqual(self.client.post('/api/ask',json=self.request()).status_code,429)
    def test_gemini_transport(self):
        import httpx
        from asyncio import run
        captured=[]
        async def handler(request):
            captured.append(request)
            return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"ok":true}'}]}}]})
        real_client=httpx.AsyncClient
        with patch('httpx.AsyncClient', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(handler),**kw)):
            result=run(main.gemini_answer({'question':'설명'},'radar'))
        self.assertTrue(result['ok'])
        self.assertEqual(captured[0].headers['x-goog-api-key'],'fake-test-key')
        self.assertNotIn('fake-test-key',str(captured[0].url))
        body=json.loads(captured[0].content)
        self.assertIn('루미',body['systemInstruction']['parts'][0]['text'])
        self.assertIn('responseJsonSchema',body['generationConfig'])
