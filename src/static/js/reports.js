var selTask;
var selName;
var selFy;
var taskList;
var taskmap = { fifocapgains:'FIFO Capital Gains', billledgercomp: 'Bill Ledger Comparison Report'};
let msgEle = document.getElementById('reports-msg');

getTasks();

window.onload = function(e) {
	//console.log("window on load");
}	

function getTasks() {
	// POST request using fetch() 
	fetch("/query", { 
      
    	// Adding method type 
	    method: "POST", 
		
    	// Adding body or contents to send 
	    //body: JSON.stringify({ 
    	//    title: "foo", 
        //	body: "bar", 
	    //    userId: 1 
    	//}), 
		
    	// Adding body or contents to send 
	    body: JSON.stringify({ 
			opcode: 1
    	}), 

	    // Adding headers to the request 
    	headers: { 
        	"Content-type": "application/json; charset=UTF-8"
	    } 
	}) 
  
	// Converting to JSON 
	.then(function (response) {
		return response.text();
	}) 
  
	// Displaying results to console 
	.then(function (text) {
    	//console.log('GET response text:');
        //console.log(text); 

		createTasks(text);
		selectTask();
	}); 
}

function createTasks(text) {

	taskList = JSON.parse(text);
	let tasksEle = document.getElementById('reports-tasks');
	
	for (let i=0; i < taskList.tasks.length; i++)
	{
		//console.log(data.tasks[i]);
		let ele = document.createElement('option');
		ele.value = taskList.tasks[i];
		ele.textContent = taskmap[ele.value];
		ele.selected = (i == 0)? true : false;
		tasksEle.appendChild(ele);
	}
}

function selectTask() {

	let option1Div = document.getElementById('reports-option1');	
	let option2Div = document.getElementById('reports-option2');	
	selTask = document.getElementById('reports-tasks').value;

	msgEle.innerHTML = '';

	if (selTask == 'billledgercomp') {

		option1Div.innerHTML = ` 
								<div class="input-group">
									<label class="input-group-text" for="reports-date">Ledger Date:</label>
									<input type="date" id="reports-date" class="form-control" name="ledger-date">
								</div>
								`
		option1Div.ClassName = "col-md-5";

		option2Div.innerHTML = ""

	} else {

		option1Div.innerHTML = `
								<input list="custnames"  id="reports-names" class="form-control" placeholder="Customer name">
								<datalist id="custnames">
								</datalist>
								`

		option1Div.ClassName = "col-md-4";

		option2Div.innerHTML = `
								<div class="input-group">
									<label class="input-group-text" for="reports-fy">FY:</label>
									<select id="reports-fy" class="form-select" name="fy">
									</select>
								</div>
								`
		let namesEle = document.getElementById('custnames');
		let fyEle = document.getElementById('reports-fy');

		for (let i=0; i < taskList.names.length; i++)
		{
			let ele = document.createElement('option');
			ele.value = taskList.names[i];
			ele.textContent = ele.value;
			namesEle.appendChild(ele);
		}

		for (let i=0; i < taskList.fy.length; i++)
		{
			//console.log(data.fy[i]);
			let ele = document.createElement('option');
			ele.value = taskList.fy[i];
			//let str = String(data.fy[i]);
			let n = parseInt(ele.value.slice(2)) + 1;
			ele.textContent = ele.value + "-" + n.toString();
			fyEle.appendChild(ele);
		}

	}
}	

function executeTask(evt) {

	let jsonBody;

	msgEle.innerHTML = '';

	evt.preventDefault(); 

	//console.log(evt);
	selTask = document.getElementById('reports-tasks').value;

	if (selTask == 'fifocapgains') {

		selName = document.getElementById('reports-names').value;
		selFy = document.getElementById('reports-fy').value;

		jsonBody = JSON.stringify({ 
					opcode: 2,
					task: selTask,
					name: selName,
					fy: selFy });

	} else if (selTask == 'billledgercomp') {

		let selDate = document.getElementById('reports-date').value;

		ledgerDate = new Date(selDate);
		//lDate.setHours(0,0,0,0);

		currentDate = new Date();
		//cDate.setHours(0,0,0,0);

		if(ledgerDate > currentDate)
		{
			msgEle.innerHTML = 'Ledger date should not be more than current date';
			return false;
		}

		jsonBody = JSON.stringify({ 
					opcode: 3,
					date: selDate });


	} else {
		msgEle.innerHTML = 'Unknown selection';
		return false;
	}

	// POST request using fetch()
	fetch("/query", { 
      
    	// Adding method type 
	    method: "POST", 
		
    	// Adding body or contents to send 
	    body: jsonBody, 

	    // Adding headers to the request 
    	headers: { 
        	"Content-type": "application/json; charset=UTF-8"
	    } 
	}) 
  
	// Converting to JSON 
	.then(function (response) {
		return response.text();
	}) 
  
	// Displaying results to console 
	.then(function (text) {

		try {
			let data = JSON.parse(text);
			console.log(data);
			showTable(data.cols, data.rows, data.xls);
		} catch(e) {
			msgEle.innerHTML = e;
		}
	}); 
}

function showTable(cols, rows, xls) {
	let colEle = document.getElementById('reports-table-head');
	let rowEle = document.getElementById('reports-table-body');

	let innerHTML = "<tr>";
	for(let i=0; i < cols.length; i++)	
	{
		col = `<th>${cols[i]}</th>`;
		innerHTML += col;

	}
	innerHTML += "</tr>";

	colEle.innerHTML = innerHTML

	innerHTML = "";
	for(let i=0; i < rows.length; i++)	
	{
		innerHTML += "<tr>";
		for(let j=0; j < rows[i].length; j++)
		{
			data = `<td>${rows[i][j]}</td>`;
			innerHTML += data;
		}
		innerHTML += "</tr>";
	}

	rowEle.innerHTML = innerHTML;
	
	xlsBtn = document.getElementById('reports-btn-xls')
    xlsBtn.classList.remove("invisible");
	xlsBtn.setAttribute("href", xls);	
}
