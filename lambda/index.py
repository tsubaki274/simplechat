# lambda/index.py
import json
import os
import re
import urllib.request
import urllib.error
from urllib.parse import urlencode

# FastAPI サーバーのURLを環境変数から取得（デフォルト値はサンプル）
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://5a38-34-19-123-204.ngrok-free.app")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # FastAPIサーバーに送信するペイロード作成
        request_payload = {
            "text": message,
            "conversation_history": conversation_history
        }
        
        # POSTリクエストの設定
        headers = {
            "Content-Type": "application/json",
        }
        
        # FastAPIサーバーにリクエストを送信
        print(f"Sending request to FastAPI server at: {FASTAPI_URL}")
        req = urllib.request.Request(
            FASTAPI_URL,
            data=json.dumps(request_payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        # リクエスト送信
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read()
                response_body = json.loads(response_data.decode('utf-8'))
                print("FastAPI response:", json.dumps(response_body))
                
                # レスポンスを取得
                assistant_response = response_body.get('response', '')
                
                if not assistant_response:
                    raise Exception("No response content from the model")
                
        except urllib.error.HTTPError as e:
            error_message = e.read().decode('utf-8')
            print(f"HTTP Error: {e.code}, {error_message}")
            raise Exception(f"FastAPI server returned error: {e.code}, {error_message}")
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
            raise Exception(f"Could not connect to FastAPI server: {e.reason}")
        
        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
