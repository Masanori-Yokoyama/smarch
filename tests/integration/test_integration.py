import os
import boto3
import pytest
from smarch.handler import lambda_handler
from smb.SMBConnection import SMBConnection

@pytest.fixture(scope="module")
def setup_environment():
    """テスト環境のセットアップ"""
    # 環境変数の設定
    os.environ['SSM_ENDPOINT_URL'] = 'http://localhost:4566'
    os.environ['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    os.environ['SMB_HOST'] = 'localhost'

    # テスト用のS3バケットを作成
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    try:
        s3.create_bucket(
            Bucket='test-bucket',
            CreateBucketConfiguration={
                'LocationConstraint': 'ap-northeast-1'
            }
        )
    except s3.exceptions.BucketAlreadyExists:
        pass

    # Parameter Storeにテスト用の認証情報を設定
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

    # テストファイルをSambaサーバーにコピー
    conn = SMBConnection('testuser', 'testpass', 'test_client', 'localhost', use_ntlm_v2=True)
    if conn.connect('localhost', 445):
        with open('tests/data/test1.txt', 'rb') as f:
            conn.storeFile('share', '/test1.txt', f)
        with open('tests/data/test2.txt', 'rb') as f:
            conn.storeFile('share', '/test2.txt', f)
        conn.close()
    
    yield
    
    # クリーンアップ
    try:
        # S3バケットのクリーンアップ
        objects = s3.list_objects_v2(Bucket='test-bucket')
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3.delete_object(Bucket='test-bucket', Key=obj['Key'])
        s3.delete_bucket(Bucket='test-bucket')

        # Parameter Storeのクリーンアップ
        ssm.delete_parameter(Name='/smb/username')
        ssm.delete_parameter(Name='/smb/password')
    except Exception as e:
        print(f"Cleanup error: {e}")

def test_end_to_end_flow(setup_environment):
    """エンドツーエンドのテスト"""
    # テスト実行前のS3バケットの状態確認
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    initial_objects = s3.list_objects_v2(Bucket='test-bucket')
    initial_count = initial_objects.get('KeyCount', 0)
    print(f"Initial S3 objects: {initial_count}")
    
    # Lambda関数実行
    result = lambda_handler({}, None)
    print("Lambda handler result:", result)
    
    # 結果の確認
    assert result['statusCode'] == 200
    
    # S3バケットの確認
    final_objects = s3.list_objects_v2(Bucket='test-bucket')
    final_count = final_objects.get('KeyCount', 0)
    print(f"Final S3 objects: {final_count}")
    assert final_count > initial_count, "ファイルがアップロードされていません"
    
    if 'Contents' in final_objects:
        for obj in final_objects['Contents']:
            print(f"Uploaded file: {obj['Key']}")