import base64
import requests

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def inference_chat(chat, API_TOKEN):    
    api_url = 'https://api.deepseek.com/chat/completions'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }

    data = {
        "model": 'deepseek-chat',
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for android UI test"}
        ],
        "max_tokens": 8192,
    }


    data["messages"].append({"role": 'user', "content": chat})

    try:
        res = requests.post(api_url, headers=headers, json=data)
        res = res.json()['choices'][0]['message']['content']
    except:
        print("Network Error:")
        print(res)

    return res

