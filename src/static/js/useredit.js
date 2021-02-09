
function checkPassword(evt) {
	//console.log(evt);
	psw = document.getElementById('pswd').value;
	psw_repeat = document.getElementById('pswd-repeat').value;

	if(psw != psw_repeat)
	{
		alert('passwords do not match');
		evt.preventDefault();
	}

}

