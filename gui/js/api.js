console.log("Loading api.js...");

// --- API Abstraction Layer ---
// These functions wrap the pywebview calls

async function checkGameStatusApi() {
    logMessage('API: Checking game status...');
    return await window.pywebview.api.check_status();
}

async function runSingleCommandApi(command) {
    logMessage(`API: Sending single command: ${command}`);
    return await window.pywebview.api.run_single_command(command);
}

async function loadPresetsApi() {
    logMessage('API: Loading battle presets...');
    return await window.pywebview.api.get_battle_presets();
}

async function runPresetBattleApi(presetName) {
    logMessage(`API: Running preset battle: ${presetName}`);
    return await window.pywebview.api.run_preset_battle(presetName);
}

async function loadItemTypesAndSubcategoriesApi() {
    logMessage('API: Loading item types and categories...');
    return await window.pywebview.api.get_item_categories_api();
}

async function loadItemsForCategoryApi(filename) {
    logMessage(`API: Loading items for category file: ${filename}`);
    return await window.pywebview.api.get_items_in_category(filename);
}

async function addItemApi(itemId, quantity) {
    logMessage(`API: Adding item: ID=${itemId}, Qty=${quantity}`);
    return await window.pywebview.api.add_item(itemId, quantity);
}

async function loadNpcsApi() {
    logMessage('API: Loading NPCs...');
    return await window.pywebview.api.get_npcs();
}

async function buildPlaceatmeCommandApi(npcId, quantity) {
    logMessage(`API: Building command for NPC ID: ${npcId}, Qty: ${quantity}`);
    return await window.pywebview.api.build_placeatme_command(npcId, quantity);
}

async function savePresetApi(presetName, commandList) {
    logMessage(`API: Saving preset: ${presetName}`);
    return await window.pywebview.api.save_battle_preset(presetName, commandList);
}

async function runCustomBattleApi(commandList) {
    logMessage(`API: Running custom battle setup (${commandList.length} commands)...`);
    return await window.pywebview.api.run_custom_battle(commandList);
}

async function loadFavoritesApi() {
    logMessage("API: Loading favorites...");
    return await window.pywebview.api.get_favorites();
}

async function saveFavoriteApi(name, command, type) {
    logMessage(`API: Attempting to save favorite '${name}'...`);
    return await window.pywebview.api.save_favorite(name, command, type);
}

async function runFavoriteApi(selectedName) {
    logMessage(`API: Running favorite: ${selectedName}...`);
    return await window.pywebview.api.run_favorite(selectedName);
}

async function deleteFavoriteApi(selectedName) {
    logMessage(`API: Deleting favorite: ${selectedName}...`);
    return await window.pywebview.api.delete_favorite(selectedName);
}

async function loadLocationCategoriesApi() {
    logMessage('API: Loading location categories...');
    return await window.pywebview.api.get_location_categories_api();
}

async function loadLocationsForCategoryApi(selectedCategoryFile) {
    logMessage(`API: Loading locations for category file: ${selectedCategoryFile}...`);
    return await window.pywebview.api.get_locations_in_category_api(selectedCategoryFile);
}

async function teleportPlayerApi(locationId) {
    logMessage(`API: Attempting to teleport to ${locationId}...`);
    return await window.pywebview.api.teleport_to_location_api(locationId);
}

console.log("api.js loaded."); 