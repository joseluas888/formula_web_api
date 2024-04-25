from flask import Flask, g, jsonify, request
from flask_cors import CORS
import oracledb
import json
# import datetime

app = Flask(__name__)
CORS(app)

types = {
    "png": "image-file-96",
    "jpg": "image-file-96",
    "jpeg": "image-file-96",
    "pdf": "pdf-96",
    "doc": "doc-96",
    "docx": "doc-96",
    "ppt": "ppt-96",
    "pptx": "ppt-96",
    "xls": "spreadsheet-file-96",
    "xlsx": "spreadsheet-file-96",
    "txt": "regular-document-96",
    "zip": "zip-96",
    "rar": "rar-96",
    "cad": "cad",
    "mp4": "video-file-96",
    "csv": "csv-96",
}

# def get_connection():
#     if 'connection' not in g:
#         connection = oracledb.connect(
#             config_dir=r"C:/opt/oracleCloud",
#             user="ADMIN",
#             password="Bannana135=+6",
#             dsn="ur7ovfu2fisfm7ve_low",
#             wallet_location=r"C:/opt/oracleCloud",
#             wallet_password="Bannana135=+6")

#         g.connection = connection
#         print("Successfully connected to Oracle Database")
#     return g.connection

def start_pool():
    # Generally a fixed-size pool is recommended, i.e. pool_min=pool_max.  Here
    # the pool contains 4 connections, which will allow 4 concurrent users.
    pool_min = 4
    pool_max = 4
    pool_inc = 0
    pool = oracledb.create_pool(
        user = "ADMIN",
        password = "Bannana135=+6",
        dsn = "ur7ovfu2fisfm7ve_low",
        min = pool_min,
        max = pool_max,
        increment = pool_inc,
        wallet_location=r"C:/opt/oracleCloud",
        config_dir=r"C:/opt/oracleCloud",
        wallet_password="Bannana135=+6",
    )
    return pool

pool = start_pool()

@app.route("/mainFolders")
def get_main_folders():
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM folders WHERE isMainFolder = 1")
            main_folders = cursor.fetchall()
            main_folders_json = []
            for folder in main_folders:
                # Get the users for this folder
                cursor.execute(f"SELECT username FROM users WHERE user_id IN (SELECT user_id FROM sharedFolders WHERE folder_id = {folder[0]})")
                users = cursor.fetchall()
                users_json = [f"assets/{user[0]}.png" for user in users]  # Replace with the actual path to the user's image

                # Get the files for this folder
                cursor.execute(f"SELECT * FROM files WHERE folder_id = {folder[0]}")
                files = cursor.fetchall()
                files_json = [{"FileId": file[0], "name": file[2]} for file in files]  # Add more file details here

                # Get the subfolders for this folder
                cursor.execute(f"SELECT * FROM folders WHERE parent_id = {folder[0]}")
                subfolders = cursor.fetchall()
                subfolders_json = []
                for subfolder in subfolders:
                    # Get the users for this subfolder
                    cursor.execute(f"SELECT * FROM users WHERE user_id IN (SELECT user_id FROM sharedFolders WHERE folder_id = {subfolder[0]})")
                    subfolder_users = cursor.fetchall()
                    subfolder_users_json = [user[0] for user in subfolder_users]  # Replace with the actual path to the user's image

                    subfolder_json = {
                        "folderId": subfolder[0],
                        "title": subfolder[2],
                        "lastModified": subfolder[3].strftime("%B %d, %Y"),
                        "users": subfolder_users_json,
                        "color": subfolder[4]
                    }
                    subfolders_json.append(subfolder_json)

                folder_json = {
                    "folderId": folder[0],
                    "title": folder[2],
                    "lastModified": folder[3].strftime("%B %d, %Y"),
                    "users": users_json,
                    "files": [],
                    "subFolders": subfolders_json,
                    "color": folder[4]
                }
                main_folders_json.append(folder_json)
            return json.dumps(main_folders_json, default=str)

@app.route("/folder/<folder_id>")
def get_folder(folder_id):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:

            # Get the folder details
            cursor.execute(f"SELECT * FROM folders WHERE folder_id = {folder_id}")
            folder = cursor.fetchone()

            # Get the users for this folder
            cursor.execute(f"SELECT * FROM users WHERE user_id IN (SELECT user_id FROM sharedFolders WHERE folder_id = {folder[0]})")
            users = cursor.fetchall()
            users_json = [user[0] for user in users]  # Replace with the actual path to the user's image

            # Get the files for this folder
            files_json = []
            cursor.execute(f"SELECT * FROM files WHERE folder_id = {folder[0]}")
            files = cursor.fetchall()
            for file in files:
                cursor.execute(f"SELECT tag FROM filetags WHERE file_id = {file[0]}")
                tags = cursor.fetchall()
                tagsJson = [tag[0] for tag in tags]
                cursor.execute(f"SELECT username FROM users WHERE user_id = {file[3]}")
                author = cursor.fetchone()
                files_json.append({
                    "FileId": file[0],
                    "name": file[2],
                    "size": file[5],
                    "author": author[0],
                    "dateAdded": file[6],
                    "icon": f"/assets/{types[file[7]]}.png",
                    "tags": tagsJson})  # Add more file details here


            # Get the subfolders for this folder
            cursor.execute(f"SELECT * FROM folders WHERE parent_id = {folder[0]}")
            subfolders = cursor.fetchall()
            subfolders_json = []
            for subfolder in subfolders:
                # Get the users for this subfolder
                cursor.execute(f"SELECT * FROM users WHERE user_id IN (SELECT user_id FROM sharedFolders WHERE folder_id = {subfolder[0]})")
                subfolder_users = cursor.fetchall()
                subfolder_users_json = [user[0] for user in subfolder_users]  # Replace with the actual path to the user's image

                subfolder_json = {
                    "folderId": subfolder[0],
                    "title": subfolder[2],
                    "lastModified": subfolder[3].strftime("%B %d, %Y"),
                    "users": subfolder_users_json,
                    "files": [],
                    "subFolders": [],
                    "color": subfolder[4]
                }
                subfolders_json.append(subfolder_json)

            folder_json = {
                "folderId": folder[0],
                "title": folder[2],
                "lastModified": folder[3].strftime("%B %d, %Y"),
                "users": users_json,
                "files": files_json,
                "subFolders": subfolders_json,
                "color": folder[4]
            }

            return json.dumps(folder_json, default=str)


@app.route("/user/<user_id>")
def get_user(user_id):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM users WHERE user_id = {user_id}")
            user = cursor.fetchone()
            if user is None:
                return jsonify({"error": "User not found"}), 404
            return json.dumps(user, default=str)
        
@app.route("/post/folder", methods=["POST"])
def post_folder():
    data = request.get_json()
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"insert into folders (parent_id, title, last_modified, color, isMainFolder) values ({data['parent_id']}, '{data['title']}', CURRENT_DATE, '{data['color']}', 0)")
            rowsAffected = cursor.rowcount
            connection.commit()
            return json.dumps({'status': 'success', 'RowsAffected': rowsAffected}, default=str)
        
@app.route("/update/folder", methods=["PUT"])
def update_folder():
    data = request.get_json()
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"update folders set title = '{data['title']}', last_modified = CURRENT_DATE, color = '{data['color']}' where folder_id = {data['folder_id']}")
            rowsAffected = cursor.rowcount
            connection.commit()
            return json.dumps({'status': 'success', 'RowsAffected': rowsAffected}, default=str)

@app.route("/files/recent")
def get_recent_files():
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"select * from files  where ROWNUM <= 10 order by date_added desc")
            recentFiles = cursor.fetchall()
            return json.dumps(recentFiles, default=str)

@app.teardown_appcontext
def close_connection(exception = None):
    connection = g.pop('connection', None)
    if connection is not None:
        connection.close()