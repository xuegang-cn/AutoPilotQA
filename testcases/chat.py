from config.contant import DS_API_KEY
from libs.MobileAgent.api import inference_chat
if __name__ == '__main__':
   res=inference_chat("hello",DS_API_KEY)
   print(res)
