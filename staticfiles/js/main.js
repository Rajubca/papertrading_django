<script>
    // Read stored theme or default to light
    const storedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-bs-theme", storedTheme);

//    if you want to use the system default
    if (storedTheme === "auto") {
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        document.documentElement.setAttribute("data-bs-theme", prefersDark ? "dark" : "light");
    }

    // Update icon
    const themeIcon = document.getElementById("themeIcon");
    if (storedTheme === "dark") {
        themeIcon.classList.replace("bi-moon-stars", "bi-sun");
    }

    // Toggle on button click
    document.getElementById("themeToggle").addEventListener("click", () => {
        let currentTheme = document.documentElement.getAttribute("data-bs-theme");
        let newTheme = currentTheme === "light" ? "dark" : "light";

        document.documentElement.setAttribute("data-bs-theme", newTheme);
        localStorage.setItem("theme", newTheme);

        // Switch icon
        if (newTheme === "dark") {
            themeIcon.classList.replace("bi-moon-stars", "bi-sun");
        } else {
            themeIcon.classList.replace("bi-sun", "bi-moon-stars");
        }
    });
</script>
