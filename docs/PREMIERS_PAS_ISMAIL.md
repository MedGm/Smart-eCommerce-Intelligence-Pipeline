# 🎯 Premiers Pas - Ismail

Bonjour Ismail ! Voici une analyse complète du projet et ce que tu dois faire en premier.

---

## 📋 Vue d'ensemble du projet

**Smart eCommerce Intelligence Pipeline** est un pipeline de données qui :
1. **Scrape** des produits depuis des boutiques Shopify et WooCommerce
2. **Nettoie et prépare** les données (preprocessing)
3. **Calcule des scores** Top-K pour identifier les meilleurs produits
4. **Applique du Machine Learning** (classification, clustering)
5. **Affiche les résultats** dans un dashboard Streamlit avec synthèse LLM

**Objectif final :** Répondre à "Quels produits sont les plus prometteurs ?" et "Quelles boutiques/catégories performent le mieux ?"

**Date limite :** 18 mai

---

## ✅ État actuel du projet

### Ce qui est déjà fait :
- ✅ Structure du projet (dossiers, fichiers de base)
- ✅ Schéma de données (`ProductRecord` dans `src/scraping/base.py`)
- ✅ Script de validation de cibles (`scripts/validate_targets.py`)
- ✅ Liste de candidats (`scripts/targets_candidates.txt`)
- ✅ Makefile avec toutes les commandes
- ✅ Structure des scrapers (mais pas encore implémentés)

### Ce qui reste à faire :
- ❌ **Phase 1.2** : Sélectionner 1 boutique Shopify + 1 boutique WooCommerce
- ❌ **Phase 2** : Implémenter les scrapers (ta responsabilité principale)
- ❌ **Phase 3-6** : Le reste du pipeline (Mohamed et toi)

---

## 🚀 TON PREMIER PAS : Phase 1.2 - Sélectionner les boutiques cibles

### Objectif
Choisir **1 boutique Shopify** et **1 boutique WooCommerce** qui seront utilisées pour le scraping.

### Critères de sélection (GO/NO-GO)

Une boutique est valide **SEULEMENT** si **TOUS** ces critères sont remplis :
- ✅ Tu peux accéder à au moins une page de liste de produits
- ✅ Tu peux accéder aux détails des produits (titre, prix, description, etc.)
- ✅ La pagination fonctionne (pages 2, 3, etc.)
- ✅ Tu estimes **au moins 300 produits** (ou 300+ au total si combiné)

### Étapes concrètes

#### Étape 1 : Valider les candidats existants

Tu as déjà une liste de candidats dans `scripts/targets_candidates.txt`. Utilise le script de validation :

```bash
# Depuis le dossier racine du projet
python scripts/validate_targets.py --input scripts/targets_candidates.txt --output target_results.csv
```

Ce script va :
- Vérifier si chaque site est accessible
- Détecter la plateforme (Shopify/WooCommerce)
- Tester les endpoints clés
- Donner un score à chaque candidat
- Générer un CSV avec les résultats

#### Étape 2 : Analyser les résultats

Ouvre `target_results.csv` et regarde :
- Les sites avec `keep=True` et `score >= 7.0`
- Les sites sans `anti_bot_hint=True`
- Les sites où `shopify_collections_all_ok=True` (Shopify) ou `woocommerce_store_api_ok=True` (WooCommerce)

#### Étape 3 : Tests manuels supplémentaires

Pour chaque candidat prometteur, teste manuellement :

**Pour Shopify :**
- Va sur `https://<site>/collections/all`
- Vérifie qu'il y a des produits visibles
- Clique sur un produit et vérifie : titre, prix, description, catégorie
- Vérifie la pagination (page 2, 3...)

**Pour WooCommerce :**
- Teste l'API publique : `https://<site>/wp-json/wc/store/v1/products?per_page=5`
- Si ça retourne du JSON avec des produits → excellent candidat !
- Sinon, teste `/shop/` et vérifie la pagination

#### Étape 4 : Sélectionner et documenter

Une fois que tu as choisi **1 Shopify** et **1 WooCommerce**, mets à jour :

1. **`docs/target_shops.md`** - Section 3 (tableau final)
2. **Créer un fichier `.env`** à la racine du projet :

```bash
# Shopify
SHOPIFY_STORE=https://ruggable.com

# WooCommerce  
WOOCOMMERCE_URL=https://danosseasoning.com
```

**Note :** Les exemples ci-dessus sont dans `target_shops.md` mais tu dois les valider toi-même !

---

## 📝 Scorecard de sélection (à remplir pour chaque candidat)

Pour chaque candidat sérieux, remplis ce tableau mentalement :

| Critère | Shopify | WooCommerce | Notes |
|---------|---------|-------------|-------|
| **Nombre estimé de produits** | _____ | _____ | Objectif ≥300 par boutique |
| **API publique fonctionne ?** | ☐ Oui ☐ Non | ☐ Oui ☐ Non | WooCommerce: `/wp-json/wc/store/v1/products` |
| **Pagination fonctionne ?** | ☐ Oui ☐ Non | ☐ Oui ☐ Non | Peux-tu accéder page 2, 3... ? |
| **Robots.txt/ToS acceptable ?** | ☐ Oui ☐ Non | ☐ Oui ☐ Non | Usage pédagogique léger OK |
| **Beaucoup de JavaScript ?** | ☐ Oui ☐ Non | ☐ Oui ☐ Non | Si oui → Playwright nécessaire |
| **Alternative disponible ?** | ☐ Oui ☐ Non | ☐ Oui ☐ Non | Ex: API échoue mais Playwright marche |

**Score (sur 10) :**
- Volume de produits : /3
- Facilité d'extraction : /3
- Stabilité : /2
- Confort légal/éthique : /1
- Valeur démo : /1

**Choisis le meilleur de chaque plateforme !**

---

## 🎯 Après la sélection : Phase 2 - Implémenter les scrapers

Une fois que tu as sélectionné tes 2 boutiques, tu dois implémenter les scrapers.

### Fichiers à modifier :

1. **`src/scraping/shopify.py`** - Implémenter `ShopifyScraper.scrape()`
2. **`src/scraping/woocommerce.py`** - Implémenter `WooCommerceScraper.scrape()`

### Ce que chaque scraper doit faire :

1. **Se connecter** à la boutique (via Playwright pour Shopify, API ou scraping pour WooCommerce)
2. **Extraire les produits** avec pagination
3. **Mapper chaque produit** vers un `ProductRecord` avec ces champs :
   - `source_platform` : "shopify" ou "woocommerce"
   - `shop_name` : nom de la boutique
   - `product_id` : ID unique
   - `product_url` : URL du produit
   - `title` : titre (requis)
   - `description` : description
   - `category` : catégorie
   - `brand` : marque
   - `price` : prix actuel
   - `old_price` : ancien prix (si promo)
   - `availability` : disponibilité
   - `rating` : note moyenne
   - `review_count` : nombre d'avis
   - `geography` : géographie
   - `scraped_at` : timestamp

4. **Sauvegarder** dans `data/raw/shopify/products.json` ou `data/raw/woocommerce/products.json`

### Objectif Phase 2 :
- ✅ Au moins **300-500 produits au total** (combiné)
- ✅ Les données correspondent au schéma `ProductRecord`
- ✅ `make scrape` fonctionne sans erreur

---

## 📚 Ressources utiles

### Documentation technique :
- **Shopify Storefront API** : https://shopify.dev/docs/storefronts/headless/building-with-the-storefront-api/getting-started
  - ⚠️ **Note importante** : L'API Storefront nécessite un token. Pour ce projet, utilise plutôt **Playwright pour scraper le storefront public**.
- **WooCommerce Store API** : `/wp-json/wc/store/v1/products` (publique, pas besoin d'auth)

### Outils de détection :
- **BuiltWith** : https://builtwith.com/ (détecter Shopify/WooCommerce)
- **Wappalyzer** : https://www.wappalyzer.com/ (extension navigateur)

### Recherche Google :
- Shopify : `site:myshopify.com "products"` ou `"powered by Shopify" "collections"`
- WooCommerce : `"powered by WooCommerce" "shop"` ou `inurl:/shop/ "WooCommerce"`

---

## ✅ Checklist de démarrage

- [ ] **Lire** ce document en entier
- [ ] **Lire** `docs/NEXT_STEPS.md` pour voir le plan complet
- [ ] **Lire** `docs/target_shops.md` pour comprendre les critères détaillés
- [ ] **Installer** les dépendances : `pip install -r requirements.txt`
- [ ] **Installer** Playwright : `playwright install chromium`
- [ ] **Exécuter** le script de validation : `python scripts/validate_targets.py --input scripts/targets_candidates.txt --output target_results.csv`
- [ ] **Analyser** les résultats et tester manuellement les meilleurs candidats
- [ ] **Sélectionner** 1 Shopify + 1 WooCommerce
- [ ] **Documenter** dans `docs/target_shops.md` (section 3)
- [ ] **Créer** le fichier `.env` avec les URLs sélectionnées
- [ ] **Discuter** avec Mohamed pour valider les choix (Phase 1.2)
- [ ] **Commencer** l'implémentation des scrapers (Phase 2)

---

## 💡 Conseils importants

1. **Ne te précipite pas** : Teste 3-5 candidats par plateforme avant de choisir
2. **Évite les sites avec Cloudflare** ou anti-bot agressifs
3. **Privilégie les sites avec beaucoup de produits** (≥300 idéalement)
4. **Pour Shopify** : Utilise Playwright pour scraper le storefront public (plus simple que l'API)
5. **Pour WooCommerce** : Si l'API Store fonctionne (`/wp-json/wc/store/v1/products`), c'est beaucoup plus facile !
6. **Documente tes choix** : Note pourquoi tu as choisi telle boutique plutôt qu'une autre

---

## 🆘 Si tu es bloqué

1. **Relis** `docs/target_shops.md` - il y a beaucoup de détails techniques
2. **Teste manuellement** dans le navigateur avant de coder
3. **Utilise le script de validation** pour filtrer rapidement les mauvais candidats
4. **Discute avec Mohamed** - c'est un projet en binôme !

---

## 📞 Prochaines étapes après Phase 1.2

Une fois que tu as sélectionné tes boutiques :
- **Phase 2** : Implémenter les scrapers (ta responsabilité principale)
- **Phase 3** : Mohamed prend le relais pour preprocessing + features
- **Phase 4** : Mohamed fait le ML/analytics
- **Phase 5** : Tu reviens pour le dashboard + LLM
- **Phase 6** : Intégration finale ensemble

---

**Bon courage Ismail ! 🚀**

Si tu as des questions, n'hésite pas à relire les docs ou à discuter avec Mohamed.

