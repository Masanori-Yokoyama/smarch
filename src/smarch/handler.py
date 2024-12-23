import os
import boto3
from smb.SMBConnection import SMBConnection
from datetime import datetime

def lambda_handler(event, context):
    """
    AWS Lambda handler for archiving files from SMB share to S3
    """
    try:
        # SMB接続の設定
        conn = SMBConnection(
            'testuser',  # TODO: Systems Manager Parameter Storeから取得
            'testpass',  # TODO: Systems Manager Parameter Storeから取得
            'lambda_client',
            'samba',
            use_ntlm_v2=True
        )
        
        # SMB接続
        if not conn.connect('samba', 445):
            return {
                'statusCode': 500,
                'body': 'Failed to connect to SMB share'
            }

        try:
            # ファイル一覧取得
            files = conn.listPath('share', '/')
            
            # S3クライアント
            s3 = boto3.client('s3')
            bucket_name = 'test-bucket'  # TODO: 環境変数から取得
            
            processed_files = []
            for file in files:
                if file.isDirectory:
                    continue
                    
                # 一時ファイルにダウンロード
                temp_path = f"/tmp/{file.filename}"
                with open(temp_path, 'wb') as f:
                    conn.retrieveFile('share', f"/{file.filename}", f)
                
                # S3にアップロード
                s3_key = f"archives/{datetime.now().strftime('%Y%m%d')}/{file.filename}"
                s3.upload_file(temp_path, bucket_name, s3_key)
                
                # 元ファイルを削除
                conn.deleteFiles('share', f"/{file.filename}")
                
                # 一時ファイルを削除
                os.remove(temp_path)
                
                processed_files.append(file.filename)
            
            return {
                'statusCode': 200,
                'body': f'Processed files: {processed_files}'
            }
                
        finally:
            conn.close()
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }