document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Clear activity select options while preserving the placeholder
      while (activitySelect.options.length > 1) {
        activitySelect.remove(1);
      }

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Build static structure and then safely insert dynamic content
        activityCard.innerHTML = `
          <h4></h4>
          <p class="activity-description"></p>
          <p class="activity-schedule"><strong>Schedule:</strong> <span class="schedule-text"></span></p>
          <p class="activity-availability"><strong>Availability:</strong> <span class="availability-text"></span></p>
          <div class="participants-section">
            <strong>Participants:</strong>
            <ul class="participants-list"></ul>
          </div>
        `;

        // Safely set text content for activity details
        const titleEl = activityCard.querySelector("h4");
        if (titleEl) {
          titleEl.textContent = name;
        }

        const descriptionEl = activityCard.querySelector(".activity-description");
        if (descriptionEl) {
          descriptionEl.textContent = details.description;
        }

        const scheduleTextEl = activityCard.querySelector(".schedule-text");
        if (scheduleTextEl) {
          scheduleTextEl.textContent = details.schedule;
        }

        const availabilityTextEl = activityCard.querySelector(".availability-text");
        if (availabilityTextEl) {
          availabilityTextEl.textContent = spotsLeft + " spots left";
        }

        // Safely populate participants list
        const participantsListEl = activityCard.querySelector(".participants-list");
        if (participantsListEl) {
          if (details.participants.length > 0) {
            details.participants.forEach(p => {
              const li = document.createElement("li");

              const span = document.createElement("span");
              span.textContent = p;
              li.appendChild(span);

              const button = document.createElement("button");
              button.className = "delete-btn";
              button.dataset.activity = name;
              button.dataset.email = p;
              button.title = "Remove participant";
              button.textContent = "✕";
              li.appendChild(button);

              participantsListEl.appendChild(li);
            });
          } else {
            const li = document.createElement("li");
            const em = document.createElement("em");
            em.textContent = "No participants yet";
            li.appendChild(em);
            participantsListEl.appendChild(li);
          }
        }
        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh the activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Handle delete button clicks
  document.addEventListener("click", async (event) => {
    if (event.target.classList.contains("delete-btn")) {
      const activity = event.target.dataset.activity;
      const email = event.target.dataset.email;

      if (confirm(`Remove ${email} from ${activity}?`)) {
        try {
          const response = await fetch(
            `/activities/${encodeURIComponent(activity)}/unsignup?email=${encodeURIComponent(email)}`,
            {
              method: "DELETE",
            }
          );

          if (response.ok) {
            // Refresh the activities list
            fetchActivities();
            messageDiv.textContent = `Successfully removed ${email}`;
            messageDiv.className = "success";
            messageDiv.classList.remove("hidden");
            setTimeout(() => {
              messageDiv.classList.add("hidden");
            }, 3000);
          } else {
            const result = await response.json();
            messageDiv.textContent = result.detail || "Failed to remove participant";
            messageDiv.className = "error";
            messageDiv.classList.remove("hidden");
          }
        } catch (error) {
          messageDiv.textContent = "Failed to remove participant. Please try again.";
          messageDiv.className = "error";
          messageDiv.classList.remove("hidden");
          console.error("Error removing participant:", error);
        }
      }
    }
  });

  // Initialize app
  fetchActivities();
});
