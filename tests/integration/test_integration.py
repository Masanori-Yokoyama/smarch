import os
import pytest
import boto3
from smarch.handler import lambda_handler

@pytest.fixture(scope="module")
def setup_environment():
    """テスト環境のセットアップ"""
    # 環境変数の設定
    os.environ['SSM_ENDPOINT_URL'] = 'http://localhost:4566'
    os.environ['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    
    # テスト用のS3バケットを作成
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    try:
        s3.create_bucket(Bucket='test-bucket')
    except s3.exceptions.BucketAlreadyExists:
        pass
    
    # テスト用のSSMパラメータを設定
    ssm = boto3.client('ssm', endpoint_url='http://localhost:4566')
    ssm.put_parameter(
        Name='/smb/username',
        Value='testuser',
        Type='SecureString',
        Overwrite=True
    )
    ssm.put_parameter(
        Name='/smb/password',
        Value='testpass',
        Type='SecureString',
        Overwrite=True
    )
    
    yield
    
    # クリーンアップ
    try:
        # S3バケットの中身を削除
        objects = s3.list_objects_v2(Bucket='test-bucket')
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3.delete_object(Bucket='test-bucket', Key=obj['Key'])
    except Exception as e:
        print(f"Cleanup error: {e}")

def test_end_to_end_flow(setup_environment):
    """エンドツーエンドのテスト"""
    # テスト実行
    result = lambda_handler({}, None)
    
    # 結果の確認
    assert result['statusCode'] == 200
    
    # S3にファイルが正しくアップロードされたか確認
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    response = s3.list_objects_v2(Bucket='test-bucket')
    
    if 'Contents' in response:
        # アップロードされたファイルの確認
        uploaded_files = [obj['Key'] for obj in response['Contents']]
        assert len(uploaded_files) > 0
        for file_key in uploaded_files:
            assert file_key.startswith('archives/')