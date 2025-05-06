console.log("Loading main.js...");

function setupEventListeners() {
    console.log("Setting up event listeners...");
    
    // --- Button Clicks ---
    if (runSingleBtn) runSingleBtn.addEventListener('click', handleRunSingleCommand);
    if (runPresetBtn) runPresetBtn.addEventListener('click', handleRunPresetBattle);
    if (addItemBtn) addItemBtn.addEventListener('click', handleAddItem);
    if (addNpcGroupBtn) addNpcGroupBtn.addEventListener('click', handleAddNpcGroup);
    if (savePresetBtn) savePresetBtn.addEventListener('click', handleSavePreset);
    if (runCustomBattleBtn) runCustomBattleBtn.addEventListener('click', handleRunCustomBattle);
    if (runFavoriteBtn) runFavoriteBtn.addEventListener('click', handleRunFavorite);
    if (deleteFavoriteBtn) deleteFavoriteBtn.addEventListener('click', handleDeleteFavorite);
    if (teleportButton) teleportButton.addEventListener('click', handleTeleportPlayer);

    // --- Select Changes ---
    if (itemTypeSelect) itemTypeSelect.addEventListener('change', handleItemTypeChange);
    if (itemCategorySelect) itemCategorySelect.addEventListener('change', handleLoadItemsForCategory);
    if (itemSelect) itemSelect.addEventListener('change', handleItemSelectionChange);
    if (favoriteSelect) favoriteSelect.addEventListener('change', handleFavoriteSelection); // UI only
    if (locationCategorySelect) locationCategorySelect.addEventListener('change', handleLoadLocationsForCategory);
    if (locationSelect) locationSelect.addEventListener('change', handleLocationSelectionChange); // UI only

    // --- Other UI Interactions ---
    // Setup collapsible sections/toggles
    setupToggleListeners(); 

     // Add listener for Enter key in command input
     if (commandInput) {
         commandInput.addEventListener('keypress', function(event) {
             if (event.key === 'Enter') {
                 event.preventDefault(); // Prevent default form submission if any
                 handleRunSingleCommand();
             }
         });
     }
     
     // Add listeners for favorite checkboxes/inputs (if needed for dynamic display)
     if (addItemSaveFavorite && addItemFavoriteName) {
         addItemSaveFavorite.addEventListener('change', (event) => {
             addItemFavoriteName.style.display = event.target.checked ? 'inline-block' : 'none';
             if(event.target.checked) addItemFavoriteName.focus();
         });
     }

    console.log("Event listeners set up.");
}

// --- Initial Load Actions --- 
function performInitialLoad() {
    logMessage('GUI Initialized and pywebview API ready.');
    try {
        logMessage('Calling initial loading functions...');
        handleCheckGameStatus(); // Use handler to update UI correctly
        handleLoadPresets();
        handleLoadItemTypes(); 
        handleLoadNpcs();
        handleLoadFavorites();
        handleLoadLocationCategories();
        updateBattleCommandDisplay(); // Initial UI state update
        logMessage('Initial loading functions called.');
    } catch (error) {
        logMessage(`Error during initial loading sequence: ${error}`, 'error');
        console.error("Initial Load Error:", error);
    }
}

// --- Main Entry Point --- 
window.addEventListener('pywebviewready', () => { 
    console.log("pywebviewready event fired.");
    setupEventListeners();
    performInitialLoad();
});

console.log("main.js loaded."); 