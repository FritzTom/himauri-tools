

async function handle() {
    const fileInput = document.getElementById("file");
    if (fileInput.files.length < 1) {
        return;
    }
    const file = fileInput.files[0];
    let data = JSON.parse(await file.text());
    const display = document.getElementById("display");
    display.innerHTML = "";
    for(let i = 0; i < data.length; i++) {
        let element = document.createElement("tr");
        let typeElement = document.createElement("th");
        let valueElement = document.createElement("td");
        typeElement.scope = "row";
        if (data[i][1] == 0) {
            typeElement.innerText = "Speech";
        }else {
            typeElement.innerText = "Choice"
        }
        element.appendChild(typeElement);
        let valueEditor = document.createElement("input");
        valueEditor.value = data[i][2];
        valueElement.appendChild(valueEditor);
        element.appendChild(valueElement);
        display.appendChild(element);
    }
}

document.getElementById("file").onchange = handle;
