echo "Starting"
# Step 1: Remove build output
rm -rf chat-ui-quince/dist

# Step 2: Remove dependencies and lock file
rm -rf chat-ui-quince/node_modules
rm -f chat-ui-quince/package-lock.json

# Step 3: (Optional) Explicitly clear Vite cache (usually in node_modules/.vite)
#rm -rf chat-ui-quince/node_modules/.vite  # Not needed if node_modules is gone
#rm -rf ~/.vite  # Rare, check if exists

echo "Finished"