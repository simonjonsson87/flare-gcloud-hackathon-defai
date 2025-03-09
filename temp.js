(function() {
    const t = document.createElement("link").relList;
    if (t && t.supports && t.supports("modulepreload"))
        return;
    for (const o of document.querySelectorAll('link[rel="modulepreload"]'))
        r(o);
    new MutationObserver(o => {
        for (const n of o)
            if (n.type === "childList")
                for (const c of n.addedNodes)
                    c.tagName === "LINK" && c.rel === "modulepreload" && r(c)
    }
    ).observe(document, {
        childList: !0,
        subtree: !0
    });
    function s(o) {
        const n = {};
        return o.integrity && (n.integrity = o.integrity),
        o.referrerPolicy && (n.referrerPolicy = o.referrerPolicy),
        o.crossOrigin === "use-credentials" ? n.credentials = "include" : o.crossOrigin === "anonymous" ? n.credentials = "omit" : n.credentials = "same-origin",
        n
    }
    function r(o) {
        if (o.ep)
            return;
        o.ep = !0;
        const n = s(o);
        fetch(o.href, n)
    }
}
)();

const g = "api/routes/chat/"
  , i = document.getElementById("chat")
  , l = document.getElementById("message-input")
  , u = document.getElementById("send-btn")
  , p = document.getElementById("google-sign-in");
window.onload = function() {
    document.getElementById("message-input").focus()
}
    ;

const a = (e, t) => {
    const s = document.createElement("div");
    s.className = `message ${t ? "user-message" : "bot-message"}`,
    s.textContent = e,
    i.appendChild(s),
    i.scrollTop = i.scrollHeight
}
  , f = async e => {
    try {
        const t = await fetch(g, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: e
            })
        });
        if (!t.ok)
            throw new Error("Network response was not ok");
        return (await t.json()).response
    } catch (t) {
        return console.error("Error:", t),
        "Sorry, there was an error processing your request. Please try again."
    }
}
  , d = async () => {
    const e = l.value.trim();
    if (e) {
        a(e, !0),
        l.value = "";
        try {
            const t = await f(e);
            console.log("Backend response:", t),
            a(t, !1)
        } catch (t) {
            console.error("Error sending input:", t),
            a("An error occurred. Please try again.", !1)
        }
    }
}
  , m = () => {}
;
console.log("Before the three event listeneers");
u.addEventListener("click", d);
p.addEventListener("click", m);
l.addEventListener("keypress", e => {
    e.key === "Enter" && !e.shiftKey && (e.preventDefault(),
    d())
}
);


const w = "api/routes/chat/";
async function y(e) {
    const s = {
        token: e.credentials
    };
    try {
        const r = await fetch(w + "verify", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(s)
        });
        if (!r.ok)
            throw new Error(`HTTP error! status: ${r.status}`);
        const o = await r.json();
        console.log("User verified:", o)
    } catch (r) {
        console.error("Sign-in failed:", r)
    }
}

window.addEventListener("load", () => {
    if (console.log("Window loaded, checking google.accounts.id:", window.google.accounts.id),
    !window.google || !window.google.accounts || !window.google.accounts.id) {
        console.error("Google Identity Services script not loaded");
        return
    }
    console.log("Before initialize, google.accounts.id:", window.google.accounts.id),
    window.google.accounts.id.initialize({
        client_id: "289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com",
        callback: y
    }),
    console.log("After initialize, google.accounts.id:", window.google.accounts.id);
    const e = document.getElementById("google-sign-in");
    e.onclick = function() {
        console.log("Before calling signIn, google.accounts.id:", window.google.accounts.id),
        console.log("Calling prompt:", window.google.accounts.id.prompt),
        window.google.accounts.id.prompt()
    }
}
);
