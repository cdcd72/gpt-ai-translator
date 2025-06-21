# gpt-ai-translator

使用 Flask、OpenAI whisper API、GPT-4.1-mini API 來開發語言翻譯 Line 機器人。  
Using Flask, OpenAI whisper API, GPT-4.1-mini API to develop line language translator.

## 使用案例

![Image](data/img/demo.png)

#### 使用指令

| 指令     | 別名             | 說明         |
| -------- | ---------------- | ------------ |
| 目前設定 | /current-setting | 查詢目前設定 |
| 設定     | /setting         | 設定語言     |

**備註：建議在手持裝置操作這些指令，因為輸入"設定"會一步步帶各位完成語言設定哦。**

#### 支援語系

| 語系     | 英文描述            |
| -------- | ------------------- |
| 繁體中文 | Traditional Chinese |
| 簡體中文 | Simplified Chinese  |
| 英文     | English             |
| 日文     | Japanese            |
| 韓文     | Korean              |
| 越南文   | Vietnamese          |
| 泰文     | Thai                |
| 印尼文   | Indonesian          |
| 義大利文 | Italian             |
| 西班牙文 | Spanish             |
| 葡萄牙文 | Portuguese          |
| 德文     | German              |
| 法文     | French              |

## 如何開始

#### 環境變數

| 名稱                                   | 預設值            | 說明                                                             |
| -------------------------------------- | ----------------- | ---------------------------------------------------------------- |
| APP_ENVIRONMENT                        | VERCEL            | 執行環境                                                         |
| APP_PUSH_TRANSLATED_TEXT_AUDIO_ENABLED | false             | 是否可以對取得的翻譯結果多推送一則語音訊息（該功能須依賴 Minio） |
| LINE_CHANNEL_ACCESS_TOKEN              | null              | LINE 的 channel access token                                     |
| LINE_CHANNEL_SECRET                    | null              | LINE 的 channel secret                                           |
| OPENAI_API_KEY                         | null              | OpenAI 的 API key                                                |
| OPENAI_COMPLETION_MODEL                | gpt-4.1-mini      | OpenAI 的交談模型                                                |
| OPENAI_COMPLETION_TEMPERATURE          | 0.2               | OpenAI 的交談模型溫度                                            |
| OPENAI_TTS_MODEL                       | gpt-4o-mini-tts   | OpenAI 的文字轉語音模型                                          |
| OPENAI_TTS_VOICE                       | alloy             | OpenAI 的文字轉語音聲音                                          |
| OPENAI_WHISPER_MODEL                   | whisper-1         | OpenAI 的語音轉文字模型                                          |
| MINIO_ENDPOINT                         | null              | Minio 的 endpoint                                                |
| MINIO_ACCESS_KEY                       | null              | Minio 的 access key                                              |
| MINIO_SECRET_KEY                       | null              | Minio 的 secret key                                              |
| MINIO_BUCKET                           | gpt-ai-translator | Minio 的 bucket 名稱                                             |

#### 部署至 Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fcdcd72%2Fgpt-ai-translator&env=LINE_CHANNEL_ACCESS_TOKEN,LINE_CHANNEL_SECRET,OPENAI_API_KEY)

## 如何偵錯

#### 調整 api/index.py 部分程式碼以可以在本機測試

```python
# from api.ai.chatgpt import ChatGPT
# from api.config.configs import *
# from api.storage.minio import MinioStorage
# from api.media.tinytag import TinyTagMedia
from ai.chatgpt import ChatGPT
from config.configs import *
from storage.minio import MinioStorage
from media.tinytag import TinyTagMedia
```

#### 依據 .env.example 格式並在根目錄新增 .env

    APP_ENVIRONMENT=DEVELOPMENT
    LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
    LINE_CHANNEL_SECRET=your_line_channel_secret
    OPENAI_API_KEY=your_openai_api_key

#### 安裝相依套件

    pip install -r requirements.txt

#### 執行 Flask

    py api/index.py

## 參考

- Line SDK : [https://github.com/line/line-bot-sdk-python](https://github.com/line/line-bot-sdk-python)
- OpenAI API Document : [https://platform.openai.com/docs/introduction](https://platform.openai.com/docs/introduction)
