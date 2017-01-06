/**
Distinct approved Hull/Character/Weaponsystem X-ups over last 90days
**/
SELECT typeName AS Hull, weaponName as WeaponSystem, COUNT(*) AS Amount
FROM (
    SELECT DISTINCT invtypes.typeName AS typeName, characters.eve_name AS name, module.typeName AS weaponName
    FROM split_fittings
    JOIN invtypes ON split_fittings.ship_type = invtypes.typeID
    JOIN fit_module ON split_fittings.id = fit_module.fitID
    JOIN invtypes AS module ON fit_module.moduleID = module.typeID
    JOIN comp_history_fits ON split_fittings.id = comp_history_fits.fitID
    JOIN comp_history ON comp_history_fits.historyID = comp_history.historyID
    JOIN characters ON comp_history.targetID = characters.id
    WHERE
     (
     /* whole entry approved */
     comp_history.action = 'comp_mv_xup_etr'
     OR
     /* single fit approved */
     comp_history.action = 'comp_mv_xup_fit'
     )
     /* yeap i don't have the invmarketgroups table in this db :( */
    AND (
     (module.marketGroupID >= 639 AND module.marketGroupID <= 644)
     OR
     (module.marketGroupID = 777) OR (module.marketGroupID = 976) OR (module.marketGroupID = 1827) OR (module.marketGroupID = 2247) OR (module.marketGroupID = 2351)
     OR 
     (module.marketGroupID >= 561 AND module.marketGroupID <= 570)
     OR
     (module.marketGroupID >= 572 AND module.marketGroupID <= 579)
     OR
     (module.marketGroupID >= 771 AND module.marketGroupID <= 776)
     )
    AND DATEDIFF(NOW(),comp_history.TIME) < 90
) AS temp
GROUP BY typeName, weaponName
ORDER BY typeName, COUNT(*) DESC;