import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("edupath.firebase")

LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "local_db.json")

class FirebaseService:
    def __init__(self):
        self.is_connected = False
        self.mode = "local_persistent"
        self.db = None
        self._local_db: Dict[str, Dict[str, Any]] = {}
        self._init_service()

    def _init_service(self):
        # Load local persistent db first to ensure availability
        self._load_local_db()

        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()
        project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()

        if cred_path and os.path.exists(cred_path):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore

                if not firebase_admin._apps:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {
                        'projectId': project_id or None
                    })
                self.db = firestore.client()
                self.is_connected = True
                self.mode = "live_firestore"
                logger.info(f"Connected to live Firebase Firestore project: {project_id or 'default'}")
            except Exception as e:
                logger.warning(f"Failed to initialize Firebase Admin SDK: {e}. Falling back to persistent local storage.")
                self.is_connected = False
                self.mode = "local_persistent"
        else:
            logger.info("FIREBASE_CREDENTIALS_PATH not set or file not found. Operating in local persistent store mode.")
            self.is_connected = False
            self.mode = "local_persistent"

    def _load_local_db(self):
        os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
        if os.path.exists(LOCAL_DB_PATH):
            try:
                with open(LOCAL_DB_PATH, "r", encoding="utf-8") as f:
                    self._local_db = json.load(f)
            except Exception as e:
                logger.error(f"Error loading {LOCAL_DB_PATH}: {e}")
                self._local_db = {}
        else:
            self._local_db = {}

    def _save_local_db(self):
        try:
            with open(LOCAL_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(self._local_db, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving to {LOCAL_DB_PATH}: {e}")

    def save(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or overwrite a document."""
        data_copy = dict(data)
        data_copy["_id"] = doc_id
        if "updated_at" not in data_copy:
            data_copy["updated_at"] = datetime.utcnow().isoformat()

        if self.is_connected and self.db:
            try:
                self.db.collection(collection).document(doc_id).set(data_copy)
                return data_copy
            except Exception as e:
                logger.error(f"Firestore save error: {e}. Falling back to local db.")

        # Local persistent fallback
        if collection not in self._local_db:
            self._local_db[collection] = {}
        self._local_db[collection][doc_id] = data_copy
        self._save_local_db()
        return data_copy

    def get(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID."""
        if self.is_connected and self.db:
            try:
                doc = self.db.collection(collection).document(doc_id).get()
                if doc.exists:
                    d = doc.to_dict()
                    d["_id"] = doc.id
                    return d
                return None
            except Exception as e:
                logger.error(f"Firestore get error: {e}. Falling back to local db.")

        col = self._local_db.get(collection, {})
        return col.get(doc_id)

    def update(self, collection: str, doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields in an existing document."""
        updates_copy = dict(updates)
        updates_copy["updated_at"] = datetime.utcnow().isoformat()

        if self.is_connected and self.db:
            try:
                self.db.collection(collection).document(doc_id).update(updates_copy)
                doc = self.db.collection(collection).document(doc_id).get()
                if doc.exists:
                    d = doc.to_dict()
                    d["_id"] = doc.id
                    return d
            except Exception as e:
                logger.error(f"Firestore update error: {e}. Falling back to local db.")

        col = self._local_db.get(collection, {})
        if doc_id in col:
            col[doc_id].update(updates_copy)
            self._save_local_db()
            return col[doc_id]
        else:
            # If doesn't exist, create it
            return self.save(collection, doc_id, updates_copy)

    def delete(self, collection: str, doc_id: str) -> bool:
        """Delete a document."""
        if self.is_connected and self.db:
            try:
                self.db.collection(collection).document(doc_id).delete()
                return True
            except Exception as e:
                logger.error(f"Firestore delete error: {e}. Falling back to local db.")

        col = self._local_db.get(collection, {})
        if doc_id in col:
            del col[doc_id]
            self._save_local_db()
            return True
        return False

    def query(self, collection: str, filters: Optional[List[tuple]] = None, order_by: Optional[str] = None, descending: bool = False, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query documents.
        filters: list of tuples: (field, op, value) where op is '==', 'in', '>', etc.
        """
        if self.is_connected and self.db:
            try:
                q = self.db.collection(collection)
                if filters:
                    for field, op, val in filters:
                        q = q.where(field, op, val)
                if order_by:
                    from firebase_admin.firestore import Query
                    direction = Query.DESCENDING if descending else Query.ASCENDING
                    q = q.order_by(order_by, direction=direction)
                if limit:
                    q = q.limit(limit)
                docs = q.stream()
                results = []
                for d in docs:
                    item = d.to_dict()
                    item["_id"] = d.id
                    results.append(item)
                return results
            except Exception as e:
                logger.error(f"Firestore query error: {e}. Falling back to local db.")

        # Local query implementation
        col = self._local_db.get(collection, {})
        results = list(col.values())

        if filters:
            for field, op, val in filters:
                if op == "==":
                    results = [item for item in results if item.get(field) == val]
                elif op == "!=":
                    results = [item for item in results if item.get(field) != val]
                elif op == "in":
                    results = [item for item in results if item.get(field) in val]
                elif op == ">=":
                    results = [item for item in results if item.get(field, 0) >= val]
                elif op == "<=":
                    results = [item for item in results if item.get(field, 0) <= val]

        if order_by:
            results.sort(key=lambda x: x.get(order_by, ""), reverse=descending)

        if limit:
            results = results[:limit]

        return results

    def query_by_user(self, collection: str, user_id: str, order_by: Optional[str] = None, descending: bool = True, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convenience query matching documents by user_id."""
        return self.query(collection, filters=[("user_id", "==", user_id)], order_by=order_by, descending=descending, limit=limit)

    def get_latest(self, collection: str, user_id: str, order_by_field: str = "created_at") -> Optional[Dict[str, Any]]:
        """Get the newest document for a user."""
        res = self.query_by_user(collection, user_id, order_by=order_by_field, descending=True, limit=1)
        return res[0] if res else None

    def get_collection_counts(self) -> Dict[str, int]:
        """Return counts of documents in all collections."""
        counts = {}
        for col_name, docs in self._local_db.items():
            counts[col_name] = len(docs)
        return counts

# Singleton instance
db_service = FirebaseService()
