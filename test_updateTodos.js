// Unit tests for updateTodos function
// Testing the incremental ID feature and other functionality

// Mock DOM elements for testing
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// Setup DOM for testing
const dom = new JSDOM('<!DOCTYPE html><html><body><div id="pendingTodos"></div><div id="completedTodos"></div></body></html>');
global.document = dom.window.document;

// Define the functions we want to test
function updateTodos(todos) {
    // Separate pending and completed todos
    const pendingTodos = todos.filter(todo => !todo.completed);
    const completedTodos = todos.filter(todo => todo.completed);
    
    // Sort pending todos by priority: high, medium, low
    const priorityOrder = { 'high': 1, 'medium': 2, 'low': 3 };
    pendingTodos.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
    
    // Update pending todos section
    const pendingTodosDiv = document.getElementById('pendingTodos');
    pendingTodosDiv.innerHTML = '<h2>Pending Tasks</h2>';
    
    if (pendingTodos.length === 0) {
        pendingTodosDiv.innerHTML += '<p>No pending tasks.</p>';
    } else {
        // Assign incremental IDs starting from 1 for pending todos
        pendingTodos.forEach((todo, index) => {
            const incrementalId = index + 1;
            const todoClass = `todo-item priority-${todo.priority}`;
            const status = '○';
            
            const todoElement = document.createElement('div');
            todoElement.className = todoClass;
            todoElement.innerHTML = `
                <strong>${status} #${incrementalId}</strong> 
                ${todo.text}
                ${todo.dueDate ? `<em>(Due: ${todo.dueDate})</em>` : ''}
                ${todo.category ? `<span>[${todo.category}]</span>` : ''}
            `;
            
            pendingTodosDiv.appendChild(todoElement);
        });
    }
    
    // Update completed todos section
    const completedTodosDiv = document.getElementById('completedTodos');
    completedTodosDiv.innerHTML = '<h2>Completed Tasks</h2>';
    
    if (completedTodos.length === 0) {
        completedTodosDiv.innerHTML += '<p>No completed tasks.</p>';
    } else {
        // Assign incremental IDs for completed todos, continuing from the last pending ID
        const startingId = pendingTodos.length + 1;
        completedTodos.forEach((todo, index) => {
            const incrementalId = startingId + index;
            const todoClass = `todo-item priority-${todo.priority} completed`;
            const status = '✓';
            
            const todoElement = document.createElement('div');
            todoElement.className = todoClass;
            todoElement.innerHTML = `
                <strong>${status} #${incrementalId}</strong> 
                ${todo.text}
                ${todo.dueDate ? `<em>(Due: ${todo.dueDate})</em>` : ''}
                ${todo.category ? `<span>[${todo.category}]</span>` : ''}
            `;
            
            completedTodosDiv.appendChild(todoElement);
        });
    }
}

// Test suite
function runTests() {
    console.log("Running unit tests for updateTodos function...\n");

    // Test 1: Incremental ID assignment for pending tasks
    console.log("Test 1: Incremental ID assignment for pending tasks");
    let testData = [
        { id: 100, text: "Task 1", completed: false, priority: "high", category: "personal" },
        { id: 200, text: "Task 2", completed: false, priority: "medium", category: "work" },
        { id: 300, text: "Task 3", completed: false, priority: "low", category: "hkma" }
    ];
    
    updateTodos(testData);
    const pendingHtml = document.getElementById('pendingTodos').innerHTML;
    const hasIncrementalIds = pendingHtml.includes("#1") && pendingHtml.includes("#2") && pendingHtml.includes("#3");
    console.log(`✓ Incremental IDs assigned correctly: ${hasIncrementalIds}\n`);

    // Test 2: Completed tasks continue ID sequence
    console.log("Test 2: Completed tasks continue ID sequence");
    testData = [
        { id: 100, text: "Task 1", completed: false, priority: "high", category: "personal" },
        { id: 200, text: "Task 2", completed: false, priority: "medium", category: "work" },
        { id: 300, text: "Task 3", completed: true, priority: "low", category: "hkma" },
        { id: 400, text: "Task 4", completed: true, priority: "high", category: "personal" }
    ];
    
    updateTodos(testData);
    const completedHtml = document.getElementById('completedTodos').innerHTML;
    const pendingHtml2 = document.getElementById('pendingTodos').innerHTML;
    const completedHasCorrectIds = completedHtml.includes("#3") && completedHtml.includes("#4"); // Should start from 3 (after 2 pending)
    const pendingHasCorrectIds = pendingHtml2.includes("#1") && pendingHtml2.includes("#2");
    console.log(`✓ Pending IDs correct: ${pendingHasCorrectIds}, Completed IDs continue sequence: ${completedHasCorrectIds}\n`);

    // Test 3: Priority sorting
    console.log("Test 3: Priority sorting (high, medium, low)");
    testData = [
        { id: 300, text: "Low Priority Task", completed: false, priority: "low", category: "personal" },
        { id: 100, text: "High Priority Task", completed: false, priority: "high", category: "work" },
        { id: 200, text: "Medium Priority Task", completed: false, priority: "medium", category: "hkma" }
    ];
    
    updateTodos(testData);
    const pendingAfterSort = document.getElementById('pendingTodos').innerHTML;
    // High priority task should appear first in HTML
    const highTaskFirst = pendingAfterSort.indexOf("High Priority Task") < pendingAfterSort.indexOf("Medium Priority Task") && 
                          pendingAfterSort.indexOf("High Priority Task") < pendingAfterSort.indexOf("Low Priority Task");
    console.log(`✓ Priority sorting works correctly: ${highTaskFirst}\n`);

    // Test 4: Empty tasks handling
    console.log("Test 4: Empty tasks handling");
    testData = [];
    updateTodos(testData);
    const emptyPendingHtml = document.getElementById('pendingTodos').innerHTML;
    const emptyCompletedHtml = document.getElementById('completedTodos').innerHTML;
    const handlesEmptyCorrectly = emptyPendingHtml.includes("No pending tasks.") && emptyCompletedHtml.includes("No completed tasks.");
    console.log(`✓ Empty tasks handled correctly: ${handlesEmptyCorrectly}\n`);

    // Test 5: Edge case - all completed tasks
    console.log("Test 5: Edge case - all completed tasks");
    testData = [
        { id: 100, text: "Completed Task 1", completed: true, priority: "high", category: "personal" },
        { id: 200, text: "Completed Task 2", completed: true, priority: "medium", category: "work" }
    ];
    
    updateTodos(testData);
    const allCompletedPending = document.getElementById('pendingTodos').innerHTML;
    const allCompletedCompleted = document.getElementById('completedTodos').innerHTML;
    const allCompletedHandles = allCompletedPending.includes("No pending tasks.") && 
                                allCompletedCompleted.includes("#1") && allCompletedCompleted.includes("#2");
    console.log(`✓ All completed tasks handled correctly: ${allCompletedHandles}\n`);

    // Test 6: Edge case - all pending tasks
    console.log("Test 6: Edge case - all pending tasks");
    testData = [
        { id: 100, text: "Pending Task 1", completed: false, priority: "low", category: "personal" },
        { id: 200, text: "Pending Task 2", completed: false, priority: "high", category: "work" }
    ];
    
    updateTodos(testData);
    const allPendingPending = document.getElementById('pendingTodos').innerHTML;
    const allPendingCompleted = document.getElementById('completedTodos').innerHTML;
    const allPendingHandles = allPendingPending.includes("#1") && allPendingPending.includes("#2") &&
                              allPendingCompleted.includes("No completed tasks.");
    console.log(`✓ All pending tasks handled correctly: ${allPendingHandles}\n`);

    console.log("All tests completed!");
}

// Run the tests
runTests();