import logging
from typing import Optional

import pymysql
from pymysql.cursors import DictCursor

from src.models.transaction import Transaction

logger = logging.getLogger(__name__)


class TiDBCloud:
    """TiDB Cloud database handler for cloud backup."""
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        ssl_ca: str,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.ssl_ca = ssl_ca
        self._init_tables()
    
    def _get_connection(self) -> pymysql.Connection:
        """Get database connection."""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            ssl_verify_cert=True,
            ssl_verify_identity=True,
            ssl_ca=self.ssl_ca,
            cursorclass=DictCursor,
        )
    
    def _init_tables(self) -> None:
        """Create tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS transactions (
                            id INT PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            type VARCHAR(10) NOT NULL,
                            amount DECIMAL(15, 2) NOT NULL,
                            category VARCHAR(50) NOT NULL,
                            description TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_user_id (user_id),
                            INDEX idx_created_at (created_at)
                        )
                    """)
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to init TiDB tables: {e}")

    
    def test_connection(self) -> bool:
        """Test if connection is available."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.warning(f"TiDB connection test failed: {e}")
            return False
    
    def insert_transaction(self, transaction: Transaction) -> bool:
        """Insert transaction to cloud. Returns True if successful."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO transactions (id, user_id, type, amount, category, description, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            type = VALUES(type),
                            amount = VALUES(amount),
                            category = VALUES(category),
                            description = VALUES(description)
                        """,
                        (
                            transaction.id,
                            transaction.user_id,
                            transaction.type,
                            transaction.amount,
                            transaction.category,
                            transaction.description,
                            transaction.created_at,
                        )
                    )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to insert to TiDB: {e}")
            return False
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete transaction from cloud. Returns True if successful."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM transactions WHERE id = %s",
                        (transaction_id,)
                    )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete from TiDB: {e}")
            return False
