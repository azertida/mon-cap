/*
  Mon cap — récolte des abris candidats sur une commune.
  Testable tel quel sur https://overpass-turbo.eu (colle, puis "Exécuter").

  Astuce robustesse : le filtre par nom peut être ambigu.
  Pour Woluwe-Saint-Lambert, on peut viser la relation administrative
  directement via son identifiant OSM (plus sûr qu'un nom) :
     area(3600000000 + 58259)->.zone;   // 58259 = relation OSM de WSL
  Si tu préfères rester lisible, garde la version par nom ci-dessous.
*/

[out:json][timeout:25];

// --- Zone : Woluwe-Saint-Lambert (commune, admin_level 8) ---
area["name"="Woluwe-Saint-Lambert"]["admin_level"="8"]->.zone;

// --- Lieux candidats comme abris ---
(
  // pharmacies (horaires réguliers seulement ; la garde du dimanche est dynamique)
  nwr["amenity"="pharmacy"](area.zone);

  // bibliothèques, bâtiments communaux, centres communautaires
  nwr["amenity"="library"](area.zone);
  nwr["amenity"="townhall"](area.zone);
  nwr["amenity"="community_centre"](area.zone);

  // galeries / grands magasins (refuges climatisés, sièges, toilettes)
  nwr["shop"="mall"](area.zone);
  nwr["shop"="department_store"](area.zone);

  // lieux de culte (frais l'été SI ouverts — à vérifier sur le terrain)
  nwr["amenity"="place_of_worship"](area.zone);
);

// "center" renvoie un point unique pour les ways/relations (bâtiments)
out center tags;
