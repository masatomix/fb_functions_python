# fb_functions_python


## セットアップ

```
% gcloud auth login
% gcloud config configurations
% gcloud config list
% gcloud config configurations list
% gcloud projects list
% gcloud config set project fb-functions-python
```

## Python環境

```
% python3 -m venv ~/venv_fb
% source ~/venv_fb/bin/activate
```


## デプロイ

```
% gcloud functions deploy vpn-check --runtime python39 --trigger-topic mainTopic --region=asia-northeast1 --entry-point=hello_pubsub
```

## TopicへのPublishで、バッチ起動

```
% gcloud pubsub topics publish mainTopic --message='testtesttest'
```


