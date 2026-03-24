import requests
import json

# 测试聊天API
url = "http://localhost:8000/api/court/chat"
headers = {"Content-Type": "application/json"}
data = {
    "minister_id": "internal",
    "message": "你好"
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    
    if response.status_code == 500:
        print("响应内容:")
        print(response.text)
    else:
        print("成功响应:")
        print(response.json())
        
except Exception as e:
    print(f"请求失败: {e}")
