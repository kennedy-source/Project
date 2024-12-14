// Ensure JavaScript runs after DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Uniform Management System is ready!');

    // Real-time search functionality
    const searchBox = document.querySelector('input[name="query"]');
    const uniformTable = document.querySelector('tbody');

    if (searchBox && uniformTable) {
        searchBox.addEventListener('input', () => {
            const searchQuery = searchBox.value.toLowerCase();
            const rows = uniformTable.querySelectorAll('tr');

            rows.forEach(row => {
                const uniformName = row.querySelector('td:first-child').textContent.toLowerCase();
                if (uniformName.includes(searchQuery)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Show modal for order placement (if modals are implemented)
    const modalTriggers = document.querySelectorAll('.order-button');
    const modal = document.getElementById('orderModal');
    const closeModal = document.getElementById('closeModal');

    if (modalTriggers && modal) {
        modalTriggers.forEach(button => {
            button.addEventListener('click', () => {
                const uniformId = button.dataset.uniformId;
                document.querySelector('#orderModal input[name="uniform_id"]').value = uniformId;
                modal.style.display = 'block';
            });
        });

        closeModal.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        window.addEventListener('click', event => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    // Add a chart to the inventory dashboard
    const inventoryChart = document.getElementById('inventoryChart');
    if (inventoryChart) {
        fetch('/api/inventory-data/')
            .then(response => response.json())
            .then(data => {
                const ctx = inventoryChart.getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.categories,
                        datasets: [{
                            label: 'Inventory Quantity',
                            data: data.quantities,
                            backgroundColor: 'rgba(0, 123, 255, 0.7)',
                            borderColor: 'rgba(0, 123, 255, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
    }
});
