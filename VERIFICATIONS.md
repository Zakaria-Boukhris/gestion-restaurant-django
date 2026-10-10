# Vérification de la préparation GitHub

- Configuration secrète déplacée vers `.env`, générée localement.
- Base SQLite d'origine et fichiers compilés exclus.
- README actualisé et deux co-auteurs crédités.
- Scripts de démonstration corrigés : aucun compte à mot de passe fixe, aucune suppression du menu existant.
- Page de connexion du personnel accessible sans session préalable.
- Installation vérifiée sous Python 3.12 / Django 5.2.18.
- Contrôle Django et migrations sur base vide : succès.
- Création des 8 tables et 25 plats de démonstration : succès.
- Réponses HTTP 200 sur accueil, menu, inscription, connexion client, connexion personnel et cinq pages d'administration après authentification.

Ces vérifications ne constituent pas un audit de sécurité ni un test complet de tous les parcours métier. Les limites connues sont décrites dans le README.
