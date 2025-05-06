console.log("Loading handlers.js...");

// --- Event Handlers ---

async function handleCheckGameStatus() {
    logMessage('Checking game status...');
    updateStatusIndicator('Checking...');
    try {
        const result = await checkGameStatusApi();
        updateStatusIndicator(result.status);
        logMessage(`Status check result: ${result.status}`);
    } catch (error) {
        setStatusIndicatorError('Error');
        logMessage(`Error checking status: ${error}`, 'error');
        console.error("Status Check Error:", error);
    }
}

async function handleRunSingleCommand() {
    const command = commandInput.value.trim();
    if (!command) {
        logMessage('Command input is empty.', 'warn');
        return;
    }
    setBatchDisabled([runSingleBtn, commandInput], true);
    logMessage(`Handling single command: ${command}`);
    try {
        const result = await runSingleCommandApi(command);
        if (result.success) {
            logMessage(`Single command executed successfully.`);
            commandInput.value = ''; 
        } else {
            logMessage(`Failed to execute single command: ${result.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        logMessage(`Error running single command: ${error}`, 'error');
         console.error("Run Single Error:", error);
    } finally {
        setBatchDisabled([runSingleBtn, commandInput], false);
        commandInput.focus();
    }
}

async function handleLoadPresets() {
    logMessage('Handling load presets...');
    populateDropdown(presetSelect, [], '-- Loading... --');
    try {
        const result = await loadPresetsApi();
        populatePresets(result.presets || []);
    } catch (error) {
        logMessage(`Error loading presets: ${error}`, 'error');
        populateDropdown(presetSelect, [], '-- Error Loading --');
    }
}

async function handleRunPresetBattle() {
    const presetName = presetSelect.value;
    if (!presetName) {
        logMessage('No preset selected.', 'warn');
        return;
    }
    setElementDisabled(runPresetBtn, true);
    logMessage(`Handling run preset: ${presetName}`);
    try {
        const result = await runPresetBattleApi(presetName);
        logMessage(`Preset execution result: ${result.success ? 'Success' : 'Failure'}${result.message ? ' (' + result.message + ')' : ''}`, result.success ? 'info' : 'error');
    } catch (error) {
        logMessage(`Error running preset battle: ${error}`, 'error');
    } finally {
        setElementDisabled(runPresetBtn, false);
        handleCheckGameStatus(); // Update status after action
    }
}

async function handleLoadItemTypes() {
    logMessage('Handling load item types...');
    populateDropdown(itemTypeSelect, [], '-- Loading... --');
    setElementDisabled(itemCategorySelect, true);
    setElementDisabled(itemSelect, true);
    setElementDisabled(addItemBtn, true);
    try {
        const result = await loadItemTypesAndSubcategoriesApi();
        populateItemTypes(result.categories || {});
    } catch (error) {
        logMessage(`Error loading item types: ${error}`, 'error');
        populateDropdown(itemTypeSelect, [], '-- Error Loading --');
    }
}

// Handler for when item type changes - delegates to UI function
function handleItemTypeChange() {
    populateItemSubcategories();
}

// Handler for when item category changes
async function handleLoadItemsForCategory() {
    const selectedFilename = itemCategorySelect.value;
    populateDropdown(itemSelect, [], '-- Loading Items... --');
    setElementDisabled(addItemBtn, true);
    displayItemDetails(null);

    if (!selectedFilename) {
        populateDropdown(itemSelect, [], '-- Select Category First --');
        return;
    }
    logMessage(`Handling load items for category: ${selectedFilename}`);
    try {
        const result = await loadItemsForCategoryApi(selectedFilename);
        populateItems(result.items || {});
    } catch (error) {
         logMessage(`Error loading items: ${error}`, 'error');
         populateDropdown(itemSelect, [], '-- Error Loading Items --');
    }
}

// Handler for when item selection changes
function handleItemSelectionChange() {
    setElementDisabled(addItemBtn, !itemSelect.value);
    const selectedOption = itemSelect.options[itemSelect.selectedIndex];
    let details = null;
    if (selectedOption && selectedOption.dataset.details) {
        try {
            details = JSON.parse(selectedOption.dataset.details);
            details.name = selectedOption.textContent; // Add name for display function
        } catch (e) {
            logMessage('Error parsing item details from dropdown', 'error');
        }
    }
    displayItemDetails(details);
}

async function handleAddItem() {
    const itemId = itemSelect.value;
    const quantity = itemQuantityInput.value;

    if (!itemId) {
        logMessage('No item selected.', 'warn');
        return;
    }
    const qtyNum = parseInt(quantity, 10);
    if (!qtyNum || qtyNum <= 0) {
        logMessage('Invalid quantity.', 'warn');
        return;
    }

    setElementDisabled(addItemBtn, true);
    logMessage(`Handling add item: ID=${itemId}, Qty=${qtyNum}`);
    try {
        const result = await addItemApi(itemId, qtyNum);
        if (result.success) {
            logMessage(`Item(s) added successfully.`);
            if (addItemSaveFavorite.checked && result.command) {
                const favName = addItemFavoriteName.value.trim();
                if (!favName) {
                    logMessage('Favorite name cannot be empty when saving.', 'warn');
                } else {
                     await handleSaveFavorite(favName, result.command, 'additem'); 
                     addItemFavoriteName.value = '';
                     addItemSaveFavorite.checked = false;
                     if(addItemFavoriteName) addItemFavoriteName.style.display = 'none';
                }
            }
        } else {
            logMessage(`Failed to add item: ${result.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        logMessage(`Error adding item: ${error}`, 'error');
    } finally {
        setElementDisabled(addItemBtn, false);
        handleCheckGameStatus();
    }
}

async function handleLoadNpcs() {
    logMessage('Handling load NPCs...');
    populateDropdown(npcSelect, [], '-- Loading... --');
    try {
        const result = await loadNpcsApi();
        populateNpcs(result.npcs || {});
    } catch (error) {
        logMessage(`Error loading NPCs: ${error}`, 'error');
        populateDropdown(npcSelect, [], '-- Error Loading NPCs --');
    }
}

async function handleAddNpcGroup() {
    const npcId = npcSelect.value;
    const quantity = npcQuantityInput.value;

    if (!npcId) {
        logMessage('No NPC selected.', 'warn');
        return;
    }
    const qtyNum = parseInt(quantity, 10);
    if (!qtyNum || qtyNum <= 0) {
        logMessage('Invalid NPC quantity.', 'warn');
        return;
    }

    setElementDisabled(addNpcGroupBtn, true);
    logMessage(`Handling add NPC group: ID=${npcId}, Qty=${qtyNum}`);
    try {
        const result = await buildPlaceatmeCommandApi(npcId, qtyNum);
        if (result.success && result.command) {
            currentBattleCommandList.push(result.command);
            logMessage(`Added command: ${result.command}`);
            updateBattleCommandDisplay();
        } else {
            logMessage(`Error building command: ${result.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        logMessage(`Error building NPC command: ${error}`, 'error');
    } finally {
        setElementDisabled(addNpcGroupBtn, false);
    }
}

async function handleSavePreset() {
    const presetName = presetNameInput.value.trim();
    if (!presetName) {
        logMessage('Preset name cannot be empty.', 'warn');
        return;
    }
    if (currentBattleCommandList.length === 0) {
        logMessage('No commands in the current setup to save.', 'warn');
        return;
    }

    setElementDisabled(savePresetBtn, true);
    logMessage(`Handling save preset: ${presetName}`);
    try {
        const result = await savePresetApi(presetName, currentBattleCommandList);
        logMessage(result.message, result.status === 'success' ? 'info' : 'error'); 
        if (result.status === 'success') {
            presetNameInput.value = '';
            await handleLoadPresets(); // Refresh list
        }
    } catch (error) {
        logMessage(`Error saving preset: ${error}`, 'error');
    } finally {
        setElementDisabled(savePresetBtn, false);
    }
}

async function handleRunCustomBattle() {
     if (currentBattleCommandList.length === 0) {
        logMessage('No commands in the current setup to run.', 'warn');
        return;
    }
    setBatchDisabled([runCustomBattleBtn, savePresetBtn, addNpcGroupBtn], true);
    logMessage(`Handling run custom battle (${currentBattleCommandList.length} commands)...`);
    try {
        const result = await runCustomBattleApi(currentBattleCommandList);
        logMessage(`Custom battle result: ${result.success ? 'Success' : 'Failure'}${result.message ? ' (' + result.message + ')' : ''}`, result.success ? 'info' : 'error');
    } catch (error) {
        logMessage(`Error running custom battle: ${error}`, 'error');
    } finally {
        setBatchDisabled([runCustomBattleBtn, addNpcGroupBtn], false);
        setElementDisabled(savePresetBtn, currentBattleCommandList.length === 0);
        handleCheckGameStatus();
    }
}

async function handleLoadFavorites() {
    logMessage("Handling load favorites...");
    populateDropdown(favoriteSelect, [], '-- Loading... --');
    setBatchDisabled([runFavoriteBtn, deleteFavoriteBtn], true);
    try {
        const result = await loadFavoritesApi();
        if (result.success && result.favorites) {
            populateFavorites(result.favorites);
             if(result.favorites.length === 0) {
                 populateDropdown(favoriteSelect, [], '-- No Favorites Saved --');
             }
        } else {
            throw new Error("Failed to load favorites or invalid data received.");
        }
    } catch (error) {
        logMessage(`Error loading favorites: ${error}`, 'error');
        populateDropdown(favoriteSelect, [], '-- Error Loading --');
        // Keep buttons disabled on error
        setBatchDisabled([runFavoriteBtn, deleteFavoriteBtn], true);
    }
}

async function handleSaveFavorite(name, command, type) {
    logMessage(`Handling save favorite '${name}'...`);
    try {
        const result = await saveFavoriteApi(name, command, type);
        logMessage(result.message || `Favorite save attempt finished. Status: ${result.status}`, result.status === 'success' ? 'info' : 'warn');
        if (result.status === 'success') {
            await handleLoadFavorites(); // Reload list on success
        }
    } catch (error) {
        logMessage(`Error calling save favorite API: ${error}`, 'error');
    }
}

async function handleRunFavorite() {
    const selectedName = favoriteSelect.value;
    if (!selectedName) {
        logMessage("No favorite selected to run.", 'warn');
        return;
    }
    setBatchDisabled([runFavoriteBtn, deleteFavoriteBtn], true);
    logMessage(`Handling run favorite: ${selectedName}...`);
    try {
        const result = await runFavoriteApi(selectedName);
        logMessage(result.message || `Favorite run attempt finished. Success: ${result.success}`, result.success ? 'info' : 'error');
    } catch (error) {
        logMessage(`Error running favorite: ${error}`, 'error');
    } finally {
        setBatchDisabled([runFavoriteBtn, deleteFavoriteBtn], false);
        handleFavoriteSelection(); // Update button state based on selection
        handleCheckGameStatus();
    }
}

async function handleDeleteFavorite() {
    const selectedName = favoriteSelect.value;
    if (!selectedName) {
        logMessage("No favorite selected to delete.", 'warn');
        return;
    }
    if (!confirm(`Are you sure you want to delete the favorite "${selectedName}"?`)) {
        return;
    }
    
    setBatchDisabled([deleteFavoriteBtn, runFavoriteBtn], true);
    logMessage(`Handling delete favorite: ${selectedName}...`);
    try {
        const result = await deleteFavoriteApi(selectedName);
        logMessage(result.message || `Favorite delete attempt finished. Success: ${result.success}`, result.success ? 'info' : 'error');
        if (result.success) {
            await handleLoadFavorites(); // Reload list
        }
    } catch (error) {
        logMessage(`Error deleting favorite: ${error}`, 'error');
    } finally {
        // Let handleLoadFavorites re-enable buttons if successful, 
        // otherwise re-enable here if an error occurred during API call
        if(!deleteFavoriteBtn.disabled) { // Check if not already handled by load success
            setBatchDisabled([deleteFavoriteBtn, runFavoriteBtn], false);
            handleFavoriteSelection();
        }
    }
}

// --- Location Handlers ---
async function handleLoadLocationCategories() {
    logMessage('Handling load location categories...');
    populateDropdown(locationCategorySelect, [], '-- Loading... --');
    populateDropdown(locationSelect, [], '-- Select Category --');
    setBatchDisabled([locationCategorySelect, locationSelect, teleportButton], true);
    try {
        const result = await loadLocationCategoriesApi();
        console.log("[HANDLER] Received categories result:", JSON.stringify(result)); 
        populateLocationCategories(result.categories || {});
    } catch (error) {
        logMessage(`Error loading location categories: ${error}`, 'error');
        populateDropdown(locationCategorySelect, [], '-- Error Loading --');
    }
}

async function handleLoadLocationsForCategory() {
    const selectedCategoryFile = locationCategorySelect.value;
    populateDropdown(locationSelect, [], '-- Loading... --');
    setBatchDisabled([locationSelect, teleportButton], true);

    if (!selectedCategoryFile) {
        populateDropdown(locationSelect, [], '-- Select Category --');
        return; 
    }

    logMessage(`Handling load locations for: ${selectedCategoryFile}...`);
    try {
        const result = await loadLocationsForCategoryApi(selectedCategoryFile);
        console.log(`[HANDLER] Received locations result for ${selectedCategoryFile}:`, JSON.stringify(result));
        populateLocations(result.locations || {});
    } catch (error) {
        logMessage(`Error loading locations: ${error}`, 'error');
        populateDropdown(locationSelect, [], '-- Error Loading --');
    }
}

// Handler for when location selection changes - delegates to UI
function handleLocationSelectionChange() {
    if (teleportButton) {
        teleportButton.disabled = !locationSelect.value;
    }
}

async function handleTeleportPlayer() {
    const locationId = locationSelect.value;
    if (!locationId) {
        logMessage('Please select a location first.', 'warning');
        return;
    }
    const locationName = locationSelect.options[locationSelect.selectedIndex].text;
    
    setBatchDisabled([teleportButton, locationCategorySelect, locationSelect], true);
    logMessage(`Handling teleport to ${locationName} (ID: ${locationId})...`);
    try {
        const result = await teleportPlayerApi(locationId);
        if (result && result.success) {
            logMessage(`Teleport command for ${locationName} sent successfully. Command: ${result.command}`, 'success');
        } else {
            const errorMsg = result ? result.message : 'Unknown error';
            logMessage(`Failed to teleport to ${locationName}: ${errorMsg}. Command: ${result?.command || 'N/A'}`, 'error');
        }
    } catch (error) {
        logMessage(`Error calling teleport API: ${error}`, 'error');
    } finally {
         setBatchDisabled([locationCategorySelect, locationSelect], false);
         handleLocationSelectionChange(); // Re-enable button based on selection
         handleCheckGameStatus();
    }
}

console.log("handlers.js loaded."); 