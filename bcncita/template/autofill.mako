<%! from bcncita import DocType, OperationType %>
// Copy the whole script to Autofill for Chrome (JavaScript type)
// and open the fast_forward_url in browser
const fast_forward_url = "https://sede.administracionespublicas.gob.es/icpplustieb/acInfo?p=${ctx.province.value}&tramite=${ctx.operation_code.value}";

const current_page = () => {
  const url = new URL(window.location.href);
  const path = url.pathname;
  return path.split("/").pop();
}

const click_on_element = (id) => {
  const el = document.getElementById(id);
  if (el !== null) { el.click(); }
}

const alarm = () => {
  const audio = new Audio("https://www.soundjay.com/transportation/car-alarm-1.wav");
  audio.play();
}

let disable_reload = false;

if (current_page() === "acInfo") {
  click_on_element("btnEntrar");
}

if (current_page() === "acEntrada") {
  % if ctx.doc_type == DocType.NIE:
  click_on_element("rdbTipoDocNie");
  % elif ctx.doc_type == DocType.PASSPORT:
  % if ctx.operation_code == OperationType.CERTIFICADOS_UE:
  click_on_element("rdbTipoDocPasDdi");
  % else:
  click_on_element("rdbTipoDocPas");
  % endif
  % elif ctx.doc_type == DocType.DNI:
  click_on_element("rdbTipoDocDni");
  % endif

  document.getElementById("txtIdCitado").value = "${ctx.doc_value}";
  document.getElementById("txtDesCitado").value = "${ctx.name}";

  % if ctx.operation_code in (OperationType.TOMA_HUELLAS, OperationType.CERTIFICADOS_UE):
  let el = document.getElementById("txtPaisNac");
  for (let i = 0, n = el.options.length; i < n; i++) {
    if (el.options[i].text === "${ctx.country}") {
      el.value = el.options[i].value;
    }
  }
  % elif ctx.operation_code in (OperationType.AUTORIZACION_DE_REGRESO, OperationType.SOLICITUD):
  document.getElementById("txtAnnoCitado").value = "${ctx.year_of_birth}";
  % endif
  setTimeout(() => { click_on_element("btnEnviar"); }, 3000);
}

if (current_page() === "acValidarEntrada") {
  setTimeout(() => { click_on_element("btnEnviar"); }, 3000);
}

if (current_page() === "acCitar") {
  let selected = false;
  let el = document.getElementById("idSede");
  if (el !== null) {
    % if ctx.offices:
    for (let i = 0, n = el.options.length; i < n; i++) {
      if (${[office.value for office in ctx.offices]}.includes(el.options[i].value)) {
        el.value = el.options[i].value;
        selected = true;
        break;
      }
    }
    % endif
    % if ctx.operation_code != OperationType.RECOGIDA_DE_TARJETA:
    if (!selected) {
      el.value = el.options[Math.floor(Math.random() * el.options.length)].value;
      selected = true;
    }
    % endif
  }
  if (selected) {
    setTimeout(() => { click_on_element("btnSiguiente"); }, 5000);
  }
}

if (current_page() === "acVerFormulario") {
  document.getElementById("txtTelefonoCitado").value = "${ctx.phone}";
  document.getElementById("emailUNO").value = "${ctx.email}";
  document.getElementById("emailDOS").value = "${ctx.email}";
  setTimeout(() => { click_on_element("btnSiguiente"); }, 3000);
}

if (current_page() === "acOfertarCita") {
  let el = document.getElementById("btnSiguiente");
  if (el !== null) {
    disable_reload = true;
    alarm();
  }
}

if (current_page() === "acVerificarCita") {
  disable_reload = true;
}

if (!disable_reload) {
    setInterval(() => {
        window.location.href = fast_forward_url;
    }, 10000);
}
