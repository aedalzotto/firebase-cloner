#!/usr/bin/python
import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import firestore
from firebase_admin import storage
from firebase_admin import exceptions
from google.cloud.firestore_v1.document import DocumentReference

def main():
	if not (sys.argv[1] and sys.argv[2]):
		print("Usage: fbclone.py <source-sdk-key.json> <dest-sdk-key.json>")
		exit()

	print("Using source credential "+sys.argv[1])
	print("Using destination credential "+sys.argv[2])

	src_cred = credentials.Certificate(sys.argv[1])
	src_app = firebase_admin.initialize_app(src_cred, name="source")

	dst_cred = credentials.Certificate(sys.argv[2])
	dst_app = firebase_admin.initialize_app(dst_cred, name="dest")

	# clone_auth(src_app, dst_app)
	clone_firestore(src_app, dst_app)


def clone_auth(src, dst):
	print("\nCloning users...")
	print("WARNING: PLEASE MANUALLY EDIT \"Sign-in method\" AND \"Templates\" FROM FIREBASE CONSOLE")

	hash_alg = auth.UserImportHash.bcrypt()
	user_list = auth.list_users(max_results=1000, app=src)

	import_list = []
	for user in user_list.users:
		iuser = auth.ImportUserRecord(user.uid, user.email, user.email_verified, user.display_name, user.phone_number, user.photo_url,
										user.disabled, user.user_metadata, None, user.custom_claims, bytes(user.password_hash.encode('ascii')), bytes(user.password_salt.encode('ascii')))
		import_list.append(iuser)

	print("\tCloning "+str(len(user_list.users))+" users...")
	try:
		result = auth.import_users(import_list, hash_alg=hash_alg, app=dst)
		for err in result.errors:
			print('Failed to import user:', err.reason)
	except exceptions.FirebaseError as error:
		print('Error importing users:', error)

	while user_list.has_next_page:
		user_list = user_list.get_next_page()

		import_list = []
		for user in user_list.users:
			iuser = auth.ImportUserRecord(user.uid, user.email, user.email_verified, user.display_name, user.phone_number, user.photo_url,
											user.disabled, user.user_metadata, None, user.custom_claims, bytes(user.password_hash.encode('ascii')), bytes(user.password_salt.encode('ascii')))
			import_list.append(iuser)

		print("\tCloning "+str(len(user_list.users))+" users...")
		try:
			result = auth.import_users(import_list, hash_alg=hash_alg, app=dst)
			for err in result.errors:
				print('Failed to import user:', err.reason)
		except exceptions.FirebaseError as error:
			print('Error importing users:', error)

def clone_firestore(src, dst):
	print("\nCloning firestore...")
	print("WARNING: PLEASE CREATE A FIRESTORE INSTANCE MANUALLY FROM CONSOLE")
	print("WARNING: PLEASE MANUALLY EDIT \"Rules\" FROM FIREBASE CONSOLE")

	src_db = firestore.client(src)
	dst_db = firestore.client(dst)

	root_cols = src_db.collections()


	for col in root_cols:
		print("\tCloning collection "+col.id)
		clone_collection(col, dst_db.collection(col.id), dst_db)


def clone_collection(src, dst, dst_root):
	doc_list = src.list_documents()
	for doc in doc_list:
		print("\t\tCloning document "+doc.id)
		doc_dict = doc.get().to_dict()
		for key in doc_dict:
			if isinstance(doc_dict[key], DocumentReference):
				doc_value = doc_dict[key]
				doc_dict[key] = dst_root.document((*doc_value._path))

		dst.document(doc.id).set(doc_dict)
		child_cols = doc.collections()
		for col in child_cols:
			print("\tCloning collection "+col.id)
			clone_collection(col, dst.document(doc.id).collection(col.id), dst_root)


if __name__== "__main__":
	main()




