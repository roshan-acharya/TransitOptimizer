console.log("TransitOptimizer frontend loaded.");


// Start button
const startButton = document.querySelector(".map-actions button.active");

startButton.addEventListener("click", () => {

    console.log("Simulation started.");

});


// Pause button
const pauseButton = document.querySelectorAll(".map-actions button")[1];

pauseButton.addEventListener("click", () => {

    console.log("Simulation paused.");

});


// Reset button
const resetButton = document.querySelectorAll(".map-actions button")[2];

resetButton.addEventListener("click", () => {

    console.log("Simulation reset.");

});


// Sidebar navigation
const navItems = document.querySelectorAll("nav a");

navItems.forEach(item => {

    item.addEventListener("click", () => {

        navItems.forEach(nav => {
            nav.classList.remove("active");
        });

        item.classList.add("active");

    });

});