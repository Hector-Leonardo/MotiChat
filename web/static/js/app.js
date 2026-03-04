firebase.initializeApp(FIREBASE_CONFIG);
const auth = firebase.auth();

let username = "";
let pollingInterval = null;
let lastMessageId = -1;
let isManualAuth = false;          // evita doble enterChat
let pendingGoogleUser = null;      // usuario Google esperando password
const POLL_DELAY = 500;

const USER_COLORS = [
    "#e06c75", "#61afef", "#98c379", "#e5c07b",
    "#c678dd", "#56b6c2", "#d19a66", "#ff75a0",
    "#69dbff", "#b4f9a0", "#ffd76e", "#cba6f7",
];
const userColorMap = {};

function getUserColor(name) {
    if (userColorMap[name]) return userColorMap[name];
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    userColorMap[name] = USER_COLORS[Math.abs(hash) % USER_COLORS.length];
    return userColorMap[name];
}

const authScreen        = document.getElementById("authScreen");
const chatScreen        = document.getElementById("chatScreen");
const verifyScreen      = document.getElementById("verifyScreen");
const messagesArea      = document.getElementById("messagesArea");
const messageInput      = document.getElementById("messageInput");
const statusDot         = document.getElementById("statusDot");
const statusText        = document.getElementById("statusText");
const authError         = document.getElementById("authError");
const headerAvatar      = document.getElementById("headerAvatar");
const verifyEmailDisplay= document.getElementById("verifyEmailDisplay");
const verifySuccess     = document.getElementById("verifySuccess");
const verifyError       = document.getElementById("verifyError");
const resendCountdown   = document.getElementById("resendCountdown");
const setPasswordScreen = document.getElementById("setPasswordScreen");
const setPwEmailDisplay = document.getElementById("setpwEmailDisplay");
const setPwSuccess      = document.getElementById("setPwSuccess");
const setPwError        = document.getElementById("setPwError");
let resendCooldown = 0;
let cooldownTimer  = null;

function switchTab(tab) {
    document.querySelectorAll(".auth-tab").forEach(t => t.classList.remove("active"));
    document.querySelector(`[data-tab="${tab}"]`).classList.add("active");
    document.getElementById("loginForm").classList.toggle("active", tab === "login");
    document.getElementById("registerForm").classList.toggle("active", tab === "register");
    hideError();
}

function showError(msg) {
    authError.textContent = msg;
    authError.classList.add("visible");
}

function hideError() {
    authError.classList.remove("visible");
}

function getFirebaseErrorMessage(code) {
    const msgs = {
        "auth/email-already-in-use":    "Este correo ya está registrado",
        "auth/invalid-email":           "Correo electrónico inválido",
        "auth/weak-password":           "La contraseña debe tener al menos 6 caracteres",
        "auth/user-not-found":          "No existe una cuenta con este correo",
        "auth/wrong-password":          "Contraseña incorrecta",
        "auth/invalid-credential":      "Credenciales incorrectas. Revisa tu correo y contraseña",
        "auth/too-many-requests":       "Demasiados intentos. Espera un momento",
        "auth/popup-closed-by-user":    "Inicio con Google cancelado",
        "auth/network-request-failed":  "Error de red. Verifica tu conexión",
        "auth/popup-blocked":           "El navegador bloqueó la ventana emergente. Permite pop-ups",
        "auth/account-exists-with-different-credential": "Ya existe una cuenta con este correo. Inicia sesión con correo y contraseña",
        "auth/credential-already-in-use": "Esta credencial ya está vinculada a otra cuenta",
        "auth/provider-already-linked":   "Este proveedor ya está vinculado a tu cuenta",
    };
    return msgs[code] || "Error de autenticación. Inténtalo de nuevo";
}

function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        btn.textContent = "\u{1F512}";
    } else {
        input.type = "password";
        btn.textContent = "\u{1F441}";
    }
}

async function handleLogin(e) {
    e.preventDefault();
    hideError();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const btn = document.getElementById("loginBtn");

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Ingresando...';
    isManualAuth = true;

    try {
        const result = await auth.signInWithEmailAndPassword(email, password);
        if (!result.user.emailVerified) { showVerifyScreen(result.user); return; }
        enterChat(result.user);
    } catch (err) {
        showError(getFirebaseErrorMessage(err.code));
    } finally {
        isManualAuth = false;
        btn.disabled = false;
        btn.textContent = "Iniciar Sesión";
    }
}

async function handleRegister(e) {
    e.preventDefault();
    hideError();
    const name     = document.getElementById("registerName").value.trim();
    const email    = document.getElementById("registerEmail").value.trim();
    const password = document.getElementById("registerPassword").value;
    const confirm  = document.getElementById("registerConfirm").value;
    const btn      = document.getElementById("registerBtn");

    if (password !== confirm) { showError("Las contraseñas no coinciden"); return; }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Creando cuenta...';
    isManualAuth = true;

    try {
        const result = await auth.createUserWithEmailAndPassword(email, password);
        await result.user.updateProfile({ displayName: name });
        await result.user.sendEmailVerification();
        showVerifyScreen(result.user);
    } catch (err) {
        showError(getFirebaseErrorMessage(err.code));
    } finally {
        isManualAuth = false;
        btn.disabled = false;
        btn.textContent = "Crear Cuenta";
    }
}

function hasPasswordProvider(user) {
    return user.providerData.some(p => p.providerId === "password");
}

async function handleGoogle() {
    hideError();
    const btn = document.getElementById("googleBtn");
    btn.disabled = true;
    isManualAuth = true;
    try {
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await auth.signInWithPopup(provider);
        const user = result.user;

        // Si ya tiene password vinculado, entra directo
        if (hasPasswordProvider(user)) {
            enterChat(user);
            return;
        }

        // Usuario Google sin password: mostrar pantalla para establecerlo
        showSetPasswordScreen(user);
    } catch (err) {
        if (err.code === "auth/account-exists-with-different-credential") {
            showError("Ya existe una cuenta con este correo. Inicia sesión con tu correo y contraseña.");
        } else {
            showError(getFirebaseErrorMessage(err.code));
        }
    } finally {
        isManualAuth = false;
        btn.disabled = false;
    }
}

function showSetPasswordScreen(user) {
    pendingGoogleUser = user;
    authScreen.style.display        = "none";
    chatScreen.style.display        = "none";
    verifyScreen.style.display      = "none";
    setPasswordScreen.style.display = "flex";
    setPwEmailDisplay.textContent   = user.email;
    setPwSuccess.classList.remove("visible");
    setPwError.classList.remove("visible");
    document.getElementById("setPwPassword").value = "";
    document.getElementById("setPwConfirm").value  = "";
}

async function handleSetPassword(e) {
    e.preventDefault();
    const password = document.getElementById("setPwPassword").value;
    const confirm  = document.getElementById("setPwConfirm").value;
    const btn      = document.getElementById("setPwBtn");

    setPwSuccess.classList.remove("visible");
    setPwError.classList.remove("visible");

    if (password !== confirm) {
        setPwError.textContent = "Las contraseñas no coinciden";
        setPwError.classList.add("visible");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Guardando...';

    try {
        const user = auth.currentUser;
        if (!user) throw new Error("Sesión expirada");

        const credential = firebase.auth.EmailAuthProvider.credential(user.email, password);
        await user.linkWithCredential(credential);

        setPwSuccess.textContent = "¡Contraseña establecida! Ahora verifica tu correo...";
        setPwSuccess.classList.add("visible");

        // Enviar correo de verificación y mostrar pantalla de verificación
        try { await user.sendEmailVerification(); } catch(e) { /* puede ya estar verificado */ }

        setTimeout(() => {
            setPasswordScreen.style.display = "none";
            pendingGoogleUser = null;
            showVerifyScreen(user);
        }, 1200);
    } catch (err) {
        if (err.code === "auth/email-already-in-use" || err.code === "auth/credential-already-in-use") {
            setPwError.textContent = "Este correo ya tiene una cuenta con contraseña. Inicia sesión normalmente.";
        } else if (err.code === "auth/provider-already-linked") {
            setPwSuccess.textContent = "Ya tienes una contraseña vinculada. ¡Entrando al chat!";
            setPwSuccess.classList.add("visible");
            setTimeout(() => {
                setPasswordScreen.style.display = "none";
                pendingGoogleUser = null;
                enterChat(auth.currentUser);
            }, 1000);
            return;
        } else if (err.code === "auth/weak-password") {
            setPwError.textContent = "La contraseña debe tener al menos 6 caracteres";
        } else {
            setPwError.textContent = err.message || "Error al establecer la contraseña";
        }
        setPwError.classList.add("visible");
    } finally {
        btn.disabled = false;
        btn.textContent = "Guardar contraseña";
    }
}

function cancelSetPassword() {
    pendingGoogleUser = null;
    auth.signOut();
    setPasswordScreen.style.display = "none";
    authScreen.style.display = "flex";
}

function showVerifyScreen(user) {
    authScreen.style.display   = "none";
    chatScreen.style.display   = "none";
    verifyScreen.style.display = "flex";
    verifyEmailDisplay.textContent = user.email;
    verifySuccess.classList.remove("visible");
    verifyError.classList.remove("visible");
    startResendCooldown();
}

async function checkVerification() {
    const btn = document.getElementById("verifyCheckBtn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Verificando...';
    verifySuccess.classList.remove("visible");
    verifyError.classList.remove("visible");

    try {
        const user = auth.currentUser;
        if (!user) { verifyError.textContent = "Sesión expirada. Vuelve a iniciar sesión."; verifyError.classList.add("visible"); return; }
        await user.reload();
        if (user.emailVerified) {
            verifySuccess.textContent = "¡Correo verificado correctamente!";
            verifySuccess.classList.add("visible");
            setTimeout(() => { verifyScreen.style.display = "none"; enterChat(user); }, 1000);
        } else {
            verifyError.textContent = "Tu correo aún no ha sido verificado. Revisa tu bandeja de entrada y spam.";
            verifyError.classList.add("visible");
        }
    } catch {
        verifyError.textContent = "Error al verificar. Inténtalo de nuevo.";
        verifyError.classList.add("visible");
    } finally {
        btn.disabled = false;
        btn.textContent = "Ya verifiqué mi correo";
    }
}

async function resendVerification() {
    if (resendCooldown > 0) return;
    const btn = document.getElementById("resendBtn");
    btn.disabled = true;
    verifySuccess.classList.remove("visible");
    verifyError.classList.remove("visible");

    try {
        const user = auth.currentUser;
        if (!user) { verifyError.textContent = "Sesión expirada. Vuelve a iniciar sesión."; verifyError.classList.add("visible"); return; }
        await user.sendEmailVerification();
        verifySuccess.textContent = "Correo de verificación reenviado exitosamente.";
        verifySuccess.classList.add("visible");
        startResendCooldown();
    } catch (err) {
        verifyError.textContent = err.code === "auth/too-many-requests"
            ? "Demasiados intentos. Espera unos minutos."
            : "Error al reenviar. Inténtalo más tarde.";
        verifyError.classList.add("visible");
    } finally {
        btn.disabled = resendCooldown > 0;
    }
}

function startResendCooldown() {
    resendCooldown = 60;
    const btn = document.getElementById("resendBtn");
    btn.disabled = true;
    if (cooldownTimer) clearInterval(cooldownTimer);
    cooldownTimer = setInterval(() => {
        resendCooldown--;
        resendCountdown.textContent = `Puedes reenviar en ${resendCooldown}s`;
        if (resendCooldown <= 0) {
            clearInterval(cooldownTimer);
            cooldownTimer = null;
            resendCountdown.textContent = "";
            btn.disabled = false;
        }
    }, 1000);
}

function backToLogin() {
    if (cooldownTimer) { clearInterval(cooldownTimer); cooldownTimer = null; }
    auth.signOut();
    verifyScreen.style.display = "none";
    authScreen.style.display   = "flex";
}

async function handleLogout() {
    try {
        if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; }
        if (cooldownTimer) { clearInterval(cooldownTimer); cooldownTimer = null; }
        await auth.signOut();
        username = "";
        lastMessageId = -1;
        messagesArea.innerHTML = "";

        // Restaurar logo MotiChat en el header
        headerAvatar.innerHTML = '<img src="/static/img/foto.png" alt="MotiChat">';

        // Resetear formularios y tabs
        document.getElementById("loginForm").reset();
        document.getElementById("registerForm").reset();
        switchTab("login");
        hideError();

        // Restaurar campos de password a tipo password
        ["loginPassword", "registerPassword", "registerConfirm"].forEach(id => {
            document.getElementById(id).type = "password";
        });
        document.querySelectorAll(".toggle-password").forEach(b => b.textContent = "\u{1F441}");

        chatScreen.style.display        = "none";
        verifyScreen.style.display      = "none";
        setPasswordScreen.style.display = "none";
        authScreen.style.display        = "flex";
        pendingGoogleUser = null;

        // Resetear pantalla set-password
        document.getElementById("setPasswordForm")?.reset();
        ["setPwPassword", "setPwConfirm"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.type = "password";
        });
    } catch (err) {
        console.error("Error al cerrar sesión:", err);
    }
}

auth.onAuthStateChanged((user) => {
    if (isManualAuth) return;  // login/register/google manual: ya se maneja
    if (user) {
        const isGoogle = user.providerData.some(p => p.providerId === "google.com");

        if (isGoogle && !hasPasswordProvider(user)) {
            // Usuario Google que aun no establecio password
            showSetPasswordScreen(user);
        } else if (isGoogle || user.emailVerified) {
            enterChat(user);
        } else {
            showVerifyScreen(user);
        }
    }
});

function enterChat(user) {
    username = user.displayName || user.email.split("@")[0];
    authScreen.style.display = "none";
    chatScreen.style.display = "flex";

    if (user.photoURL) {
        headerAvatar.innerHTML = `<img class="user-photo" src="${user.photoURL}" alt="">`;
    } else {
        headerAvatar.textContent = username.charAt(0).toUpperCase();
    }

    addSystemMessage(`${username} se unió al chat`);
    checkStatus();
    if (!pollingInterval) startPolling();
    messageInput.focus();
}

messageInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendMessage(); });

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    messageInput.value = "";
    try {
        const r = await fetch("/api/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: username, message: text }),
        });
        if (!r.ok) addSystemMessage("Error al enviar");
    } catch { addSystemMessage("Sin conexión"); }
}

function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(async () => {
        try {
            const r = await fetch(`/api/messages?since=${lastMessageId}`);
            const data = await r.json();
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach((msg) => {
                    addMessage(msg.user, msg.message, msg.timestamp);
                    if (msg.id !== undefined && msg.id > lastMessageId) lastMessageId = msg.id;
                });
            }
            updateStatus(true);
        } catch { updateStatus(false); }
    }, POLL_DELAY);
}

async function checkStatus() {
    try {
        const r = await fetch("/api/status");
        const d = await r.json();
        updateStatus(d.grpc_connected);
    } catch { updateStatus(false); }
}

function updateStatus(ok) {
    statusDot.classList.toggle("connected", ok);
    statusText.textContent = ok ? "en línea" : "desconectado";
}

function addMessage(user, message, timestamp) {
    const div = document.createElement("div");
    const isMine = user === username;
    div.className = `message ${isMine ? "sent" : "received"}`;

    let timeStr = "";
    if (timestamp) {
        const p = timestamp.split(" ");
        timeStr = p.length > 1 ? p[1].substring(0, 5) : timestamp;
    }

    const color = getUserColor(user);
    div.innerHTML = `
        ${!isMine ? `<div class="msg-user" style="color:${color}">${esc(user)}</div>` : ""}
        <div class="msg-text">${esc(message)}</div>
        <div class="msg-time">${timeStr}</div>
    `;
    messagesArea.appendChild(div);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function addSystemMessage(text) {
    const div = document.createElement("div");
    div.className = "message system";
    div.textContent = text;
    messagesArea.appendChild(div);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function esc(t) {
    const d = document.createElement("div");
    d.textContent = t;
    return d.innerHTML;
}
