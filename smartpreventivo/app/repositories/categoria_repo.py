"""
CategoriaRepository
Gestisce le operazioni DB per CategoriaLavoro e Domanda.
"""

from app.models import db, CategoriaLavoro, Domanda


class CategoriaRepository:

    @staticmethod
    def get_all_attive():
        """Restituisce tutte le categorie attive."""
        return CategoriaLavoro.query.filter_by(attiva=True).all()

    @staticmethod
    def get_by_id(cat_id):
        """Recupera una categoria tramite ID."""
        return CategoriaLavoro.query.get(cat_id)

    @staticmethod
    def get_domande(categoria_id):
        """Restituisce le domande di una categoria, ordinate."""
        return (Domanda.query
                .filter_by(categoria_id=categoria_id)
                .order_by(Domanda.ordine)
                .all())

    @staticmethod
    def get_domanda_by_id(domanda_id):
        return Domanda.query.get(domanda_id)
