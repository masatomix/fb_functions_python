# fb_functions_python


## セットアップ

```
% gcloud auth login
% gcloud projects list
% gcloud config configurations list
% gcloud config list
% gcloud config set project fb-functions-python
% gcloud config configurations list
% gcloud config list
```

## Python環境

```
% python3 -m venv ~/venv_fb
% source ~/venv_fb/bin/activate
```


## デプロイ

- mainTopicへのPublishをトリガーに起動する関数を作成。
- 名前はvpn-checkで、具体的な関数名はexecute 
- python 3.9 で動かす。regionはTokyo

```
% gcloud functions deploy vpn-check --runtime python39 --trigger-topic mainTopic --region=asia-northeast1 --entry-point=execute
```

## TopicへのPublishで、バッチ起動

```
% gcloud pubsub topics publish mainTopic --message='testtesttest'
```


