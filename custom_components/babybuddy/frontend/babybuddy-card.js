/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Q = globalThis, lt = Q.ShadowRoot && (Q.ShadyCSS === void 0 || Q.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, ct = Symbol(), pt = /* @__PURE__ */ new WeakMap();
let Tt = class {
  constructor(t, i, r) {
    if (this._$cssResult$ = !0, r !== ct) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = i;
  }
  get styleSheet() {
    let t = this.o;
    const i = this.t;
    if (lt && t === void 0) {
      const r = i !== void 0 && i.length === 1;
      r && (t = pt.get(i)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), r && pt.set(i, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const Pt = (e) => new Tt(typeof e == "string" ? e : e + "", void 0, ct), F = (e, ...t) => {
  const i = e.length === 1 ? e[0] : t.reduce((r, s, o) => r + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s) + e[o + 1], e[0]);
  return new Tt(i, e, ct);
}, Rt = (e, t) => {
  if (lt) e.adoptedStyleSheets = t.map((i) => i instanceof CSSStyleSheet ? i : i.styleSheet);
  else for (const i of t) {
    const r = document.createElement("style"), s = Q.litNonce;
    s !== void 0 && r.setAttribute("nonce", s), r.textContent = i.cssText, e.appendChild(r);
  }
}, ut = lt ? (e) => e : (e) => e instanceof CSSStyleSheet ? ((t) => {
  let i = "";
  for (const r of t.cssRules) i += r.cssText;
  return Pt(i);
})(e) : e;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Ot, defineProperty: Mt, getOwnPropertyDescriptor: zt, getOwnPropertyNames: Ut, getOwnPropertySymbols: Nt, getPrototypeOf: jt } = Object, C = globalThis, ft = C.trustedTypes, Lt = ft ? ft.emptyScript : "", rt = C.reactiveElementPolyfillSupport, W = (e, t) => e, tt = { toAttribute(e, t) {
  switch (t) {
    case Boolean:
      e = e ? Lt : null;
      break;
    case Object:
    case Array:
      e = e == null ? e : JSON.stringify(e);
  }
  return e;
}, fromAttribute(e, t) {
  let i = e;
  switch (t) {
    case Boolean:
      i = e !== null;
      break;
    case Number:
      i = e === null ? null : Number(e);
      break;
    case Object:
    case Array:
      try {
        i = JSON.parse(e);
      } catch {
        i = null;
      }
  }
  return i;
} }, dt = (e, t) => !Ot(e, t), mt = { attribute: !0, type: String, converter: tt, reflect: !1, useDefault: !1, hasChanged: dt };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), C.litPropertyMetadata ?? (C.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let U = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, i = mt) {
    if (i.state && (i.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((i = Object.create(i)).wrapped = !0), this.elementProperties.set(t, i), !i.noAccessor) {
      const r = Symbol(), s = this.getPropertyDescriptor(t, r, i);
      s !== void 0 && Mt(this.prototype, t, s);
    }
  }
  static getPropertyDescriptor(t, i, r) {
    const { get: s, set: o } = zt(this.prototype, t) ?? { get() {
      return this[i];
    }, set(n) {
      this[i] = n;
    } };
    return { get: s, set(n) {
      const a = s == null ? void 0 : s.call(this);
      o == null || o.call(this, n), this.requestUpdate(t, a, r);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? mt;
  }
  static _$Ei() {
    if (this.hasOwnProperty(W("elementProperties"))) return;
    const t = jt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(W("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(W("properties"))) {
      const i = this.properties, r = [...Ut(i), ...Nt(i)];
      for (const s of r) this.createProperty(s, i[s]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const i = litPropertyMetadata.get(t);
      if (i !== void 0) for (const [r, s] of i) this.elementProperties.set(r, s);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [i, r] of this.elementProperties) {
      const s = this._$Eu(i, r);
      s !== void 0 && this._$Eh.set(s, i);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const i = [];
    if (Array.isArray(t)) {
      const r = new Set(t.flat(1 / 0).reverse());
      for (const s of r) i.unshift(ut(s));
    } else t !== void 0 && i.push(ut(t));
    return i;
  }
  static _$Eu(t, i) {
    const r = i.attribute;
    return r === !1 ? void 0 : typeof r == "string" ? r : typeof t == "string" ? t.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var t;
    this._$ES = new Promise((i) => this.enableUpdating = i), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (t = this.constructor.l) == null || t.forEach((i) => i(this));
  }
  addController(t) {
    var i;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t), this.renderRoot !== void 0 && this.isConnected && ((i = t.hostConnected) == null || i.call(t));
  }
  removeController(t) {
    var i;
    (i = this._$EO) == null || i.delete(t);
  }
  _$E_() {
    const t = /* @__PURE__ */ new Map(), i = this.constructor.elementProperties;
    for (const r of i.keys()) this.hasOwnProperty(r) && (t.set(r, this[r]), delete this[r]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return Rt(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    var t;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (t = this._$EO) == null || t.forEach((i) => {
      var r;
      return (r = i.hostConnected) == null ? void 0 : r.call(i);
    });
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    var t;
    (t = this._$EO) == null || t.forEach((i) => {
      var r;
      return (r = i.hostDisconnected) == null ? void 0 : r.call(i);
    });
  }
  attributeChangedCallback(t, i, r) {
    this._$AK(t, r);
  }
  _$ET(t, i) {
    var o;
    const r = this.constructor.elementProperties.get(t), s = this.constructor._$Eu(t, r);
    if (s !== void 0 && r.reflect === !0) {
      const n = (((o = r.converter) == null ? void 0 : o.toAttribute) !== void 0 ? r.converter : tt).toAttribute(i, r.type);
      this._$Em = t, n == null ? this.removeAttribute(s) : this.setAttribute(s, n), this._$Em = null;
    }
  }
  _$AK(t, i) {
    var o, n;
    const r = this.constructor, s = r._$Eh.get(t);
    if (s !== void 0 && this._$Em !== s) {
      const a = r.getPropertyOptions(s), l = typeof a.converter == "function" ? { fromAttribute: a.converter } : ((o = a.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? a.converter : tt;
      this._$Em = s;
      const d = l.fromAttribute(i, a.type);
      this[s] = d ?? ((n = this._$Ej) == null ? void 0 : n.get(s)) ?? d, this._$Em = null;
    }
  }
  requestUpdate(t, i, r, s = !1, o) {
    var n;
    if (t !== void 0) {
      const a = this.constructor;
      if (s === !1 && (o = this[t]), r ?? (r = a.getPropertyOptions(t)), !((r.hasChanged ?? dt)(o, i) || r.useDefault && r.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(t)) && !this.hasAttribute(a._$Eu(t, r)))) return;
      this.C(t, i, r);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, i, { useDefault: r, reflect: s, wrapped: o }, n) {
    r && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t) && (this._$Ej.set(t, n ?? i ?? this[t]), o !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || r || (i = void 0), this._$AL.set(t, i)), s === !0 && this._$Em !== t && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (i) {
      Promise.reject(i);
    }
    const t = this.scheduleUpdate();
    return t != null && await t, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var r;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [o, n] of this._$Ep) this[o] = n;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [o, n] of s) {
        const { wrapped: a } = n, l = this[o];
        a !== !0 || this._$AL.has(o) || l === void 0 || this.C(o, void 0, n, l);
      }
    }
    let t = !1;
    const i = this._$AL;
    try {
      t = this.shouldUpdate(i), t ? (this.willUpdate(i), (r = this._$EO) == null || r.forEach((s) => {
        var o;
        return (o = s.hostUpdate) == null ? void 0 : o.call(s);
      }), this.update(i)) : this._$EM();
    } catch (s) {
      throw t = !1, this._$EM(), s;
    }
    t && this._$AE(i);
  }
  willUpdate(t) {
  }
  _$AE(t) {
    var i;
    (i = this._$EO) == null || i.forEach((r) => {
      var s;
      return (s = r.hostUpdated) == null ? void 0 : s.call(r);
    }), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t) {
    return !0;
  }
  update(t) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((i) => this._$ET(i, this[i]))), this._$EM();
  }
  updated(t) {
  }
  firstUpdated(t) {
  }
};
U.elementStyles = [], U.shadowRootOptions = { mode: "open" }, U[W("elementProperties")] = /* @__PURE__ */ new Map(), U[W("finalized")] = /* @__PURE__ */ new Map(), rt == null || rt({ ReactiveElement: U }), (C.reactiveElementVersions ?? (C.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Y = globalThis, _t = (e) => e, et = Y.trustedTypes, bt = et ? et.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, kt = "$lit$", k = `lit$${Math.random().toFixed(9).slice(2)}$`, Ct = "?" + k, Ht = `<${Ct}>`, R = document, V = () => R.createComment(""), q = (e) => e === null || typeof e != "object" && typeof e != "function", ht = Array.isArray, Ft = (e) => ht(e) || typeof (e == null ? void 0 : e[Symbol.iterator]) == "function", ot = `[ 	
\f\r]`, K = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, gt = /-->/g, yt = />/g, D = RegExp(`>|${ot}(?:([^\\s"'>=/]+)(${ot}*=${ot}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), vt = /'/g, $t = /"/g, Dt = /^(?:script|style|textarea|title)$/i, Gt = (e) => (t, ...i) => ({ _$litType$: e, strings: t, values: i }), c = Gt(1), N = Symbol.for("lit-noChange"), h = Symbol.for("lit-nothing"), xt = /* @__PURE__ */ new WeakMap(), I = R.createTreeWalker(R, 129);
function It(e, t) {
  if (!ht(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return bt !== void 0 ? bt.createHTML(t) : t;
}
const Bt = (e, t) => {
  const i = e.length - 1, r = [];
  let s, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = K;
  for (let a = 0; a < i; a++) {
    const l = e[a];
    let d, p, u = -1, b = 0;
    for (; b < l.length && (n.lastIndex = b, p = n.exec(l), p !== null); ) b = n.lastIndex, n === K ? p[1] === "!--" ? n = gt : p[1] !== void 0 ? n = yt : p[2] !== void 0 ? (Dt.test(p[2]) && (s = RegExp("</" + p[2], "g")), n = D) : p[3] !== void 0 && (n = D) : n === D ? p[0] === ">" ? (n = s ?? K, u = -1) : p[1] === void 0 ? u = -2 : (u = n.lastIndex - p[2].length, d = p[1], n = p[3] === void 0 ? D : p[3] === '"' ? $t : vt) : n === $t || n === vt ? n = D : n === gt || n === yt ? n = K : (n = D, s = void 0);
    const x = n === D && e[a + 1].startsWith("/>") ? " " : "";
    o += n === K ? l + Ht : u >= 0 ? (r.push(d), l.slice(0, u) + kt + l.slice(u) + k + x) : l + k + (u === -2 ? a : x);
  }
  return [It(e, o + (e[i] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
};
class X {
  constructor({ strings: t, _$litType$: i }, r) {
    let s;
    this.parts = [];
    let o = 0, n = 0;
    const a = t.length - 1, l = this.parts, [d, p] = Bt(t, i);
    if (this.el = X.createElement(d, r), I.currentNode = this.el.content, i === 2 || i === 3) {
      const u = this.el.content.firstChild;
      u.replaceWith(...u.childNodes);
    }
    for (; (s = I.nextNode()) !== null && l.length < a; ) {
      if (s.nodeType === 1) {
        if (s.hasAttributes()) for (const u of s.getAttributeNames()) if (u.endsWith(kt)) {
          const b = p[n++], x = s.getAttribute(u).split(k), M = /([.?@])?(.*)/.exec(b);
          l.push({ type: 1, index: o, name: M[2], strings: x, ctor: M[1] === "." ? Wt : M[1] === "?" ? Yt : M[1] === "@" ? Vt : it }), s.removeAttribute(u);
        } else u.startsWith(k) && (l.push({ type: 6, index: o }), s.removeAttribute(u));
        if (Dt.test(s.tagName)) {
          const u = s.textContent.split(k), b = u.length - 1;
          if (b > 0) {
            s.textContent = et ? et.emptyScript : "";
            for (let x = 0; x < b; x++) s.append(u[x], V()), I.nextNode(), l.push({ type: 2, index: ++o });
            s.append(u[b], V());
          }
        }
      } else if (s.nodeType === 8) if (s.data === Ct) l.push({ type: 2, index: o });
      else {
        let u = -1;
        for (; (u = s.data.indexOf(k, u + 1)) !== -1; ) l.push({ type: 7, index: o }), u += k.length - 1;
      }
      o++;
    }
  }
  static createElement(t, i) {
    const r = R.createElement("template");
    return r.innerHTML = t, r;
  }
}
function j(e, t, i = e, r) {
  var n, a;
  if (t === N) return t;
  let s = r !== void 0 ? (n = i._$Co) == null ? void 0 : n[r] : i._$Cl;
  const o = q(t) ? void 0 : t._$litDirective$;
  return (s == null ? void 0 : s.constructor) !== o && ((a = s == null ? void 0 : s._$AO) == null || a.call(s, !1), o === void 0 ? s = void 0 : (s = new o(e), s._$AT(e, i, r)), r !== void 0 ? (i._$Co ?? (i._$Co = []))[r] = s : i._$Cl = s), s !== void 0 && (t = j(e, s._$AS(e, t.values), s, r)), t;
}
class Kt {
  constructor(t, i) {
    this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = i;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const { el: { content: i }, parts: r } = this._$AD, s = ((t == null ? void 0 : t.creationScope) ?? R).importNode(i, !0);
    I.currentNode = s;
    let o = I.nextNode(), n = 0, a = 0, l = r[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let d;
        l.type === 2 ? d = new J(o, o.nextSibling, this, t) : l.type === 1 ? d = new l.ctor(o, l.name, l.strings, this, t) : l.type === 6 && (d = new qt(o, this, t)), this._$AV.push(d), l = r[++a];
      }
      n !== (l == null ? void 0 : l.index) && (o = I.nextNode(), n++);
    }
    return I.currentNode = R, s;
  }
  p(t) {
    let i = 0;
    for (const r of this._$AV) r !== void 0 && (r.strings !== void 0 ? (r._$AI(t, r, i), i += r.strings.length - 2) : r._$AI(t[i])), i++;
  }
}
class J {
  get _$AU() {
    var t;
    return ((t = this._$AM) == null ? void 0 : t._$AU) ?? this._$Cv;
  }
  constructor(t, i, r, s) {
    this.type = 2, this._$AH = h, this._$AN = void 0, this._$AA = t, this._$AB = i, this._$AM = r, this.options = s, this._$Cv = (s == null ? void 0 : s.isConnected) ?? !0;
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const i = this._$AM;
    return i !== void 0 && (t == null ? void 0 : t.nodeType) === 11 && (t = i.parentNode), t;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, i = this) {
    t = j(this, t, i), q(t) ? t === h || t == null || t === "" ? (this._$AH !== h && this._$AR(), this._$AH = h) : t !== this._$AH && t !== N && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Ft(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== h && q(this._$AH) ? this._$AA.nextSibling.data = t : this.T(R.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    var o;
    const { values: i, _$litType$: r } = t, s = typeof r == "number" ? this._$AC(t) : (r.el === void 0 && (r.el = X.createElement(It(r.h, r.h[0]), this.options)), r);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === s) this._$AH.p(i);
    else {
      const n = new Kt(s, this), a = n.u(this.options);
      n.p(i), this.T(a), this._$AH = n;
    }
  }
  _$AC(t) {
    let i = xt.get(t.strings);
    return i === void 0 && xt.set(t.strings, i = new X(t)), i;
  }
  k(t) {
    ht(this._$AH) || (this._$AH = [], this._$AR());
    const i = this._$AH;
    let r, s = 0;
    for (const o of t) s === i.length ? i.push(r = new J(this.O(V()), this.O(V()), this, this.options)) : r = i[s], r._$AI(o), s++;
    s < i.length && (this._$AR(r && r._$AB.nextSibling, s), i.length = s);
  }
  _$AR(t = this._$AA.nextSibling, i) {
    var r;
    for ((r = this._$AP) == null ? void 0 : r.call(this, !1, !0, i); t !== this._$AB; ) {
      const s = _t(t).nextSibling;
      _t(t).remove(), t = s;
    }
  }
  setConnected(t) {
    var i;
    this._$AM === void 0 && (this._$Cv = t, (i = this._$AP) == null || i.call(this, t));
  }
}
class it {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, i, r, s, o) {
    this.type = 1, this._$AH = h, this._$AN = void 0, this.element = t, this.name = i, this._$AM = s, this.options = o, r.length > 2 || r[0] !== "" || r[1] !== "" ? (this._$AH = Array(r.length - 1).fill(new String()), this.strings = r) : this._$AH = h;
  }
  _$AI(t, i = this, r, s) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) t = j(this, t, i, 0), n = !q(t) || t !== this._$AH && t !== N, n && (this._$AH = t);
    else {
      const a = t;
      let l, d;
      for (t = o[0], l = 0; l < o.length - 1; l++) d = j(this, a[r + l], i, l), d === N && (d = this._$AH[l]), n || (n = !q(d) || d !== this._$AH[l]), d === h ? t = h : t !== h && (t += (d ?? "") + o[l + 1]), this._$AH[l] = d;
    }
    n && !s && this.j(t);
  }
  j(t) {
    t === h ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Wt extends it {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === h ? void 0 : t;
  }
}
class Yt extends it {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== h);
  }
}
class Vt extends it {
  constructor(t, i, r, s, o) {
    super(t, i, r, s, o), this.type = 5;
  }
  _$AI(t, i = this) {
    if ((t = j(this, t, i, 0) ?? h) === N) return;
    const r = this._$AH, s = t === h && r !== h || t.capture !== r.capture || t.once !== r.once || t.passive !== r.passive, o = t !== h && (r === h || s);
    s && this.element.removeEventListener(this.name, this, r), o && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    var i;
    typeof this._$AH == "function" ? this._$AH.call(((i = this.options) == null ? void 0 : i.host) ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class qt {
  constructor(t, i, r) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = i, this.options = r;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    j(this, t);
  }
}
const nt = Y.litHtmlPolyfillSupport;
nt == null || nt(X, J), (Y.litHtmlVersions ?? (Y.litHtmlVersions = [])).push("3.3.2");
const Xt = (e, t, i) => {
  const r = (i == null ? void 0 : i.renderBefore) ?? t;
  let s = r._$litPart$;
  if (s === void 0) {
    const o = (i == null ? void 0 : i.renderBefore) ?? null;
    r._$litPart$ = s = new J(t.insertBefore(V(), o), o, void 0, i ?? {});
  }
  return s._$AI(e), s;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const P = globalThis;
class E extends U {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var i;
    const t = super.createRenderRoot();
    return (i = this.renderOptions).renderBefore ?? (i.renderBefore = t.firstChild), t;
  }
  update(t) {
    const i = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Xt(i, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var t;
    super.connectedCallback(), (t = this._$Do) == null || t.setConnected(!0);
  }
  disconnectedCallback() {
    var t;
    super.disconnectedCallback(), (t = this._$Do) == null || t.setConnected(!1);
  }
  render() {
    return N;
  }
}
var St;
E._$litElement$ = !0, E.finalized = !0, (St = P.litElementHydrateSupport) == null || St.call(P, { LitElement: E });
const at = P.litElementPolyfillSupport;
at == null || at({ LitElement: E });
(P.litElementVersions ?? (P.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const G = (e) => (t, i) => {
  i !== void 0 ? i.addInitializer(() => {
    customElements.define(e, t);
  }) : customElements.define(e, t);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Jt = { attribute: !0, type: String, converter: tt, reflect: !1, hasChanged: dt }, Zt = (e = Jt, t, i) => {
  const { kind: r, metadata: s } = i;
  let o = globalThis.litPropertyMetadata.get(s);
  if (o === void 0 && globalThis.litPropertyMetadata.set(s, o = /* @__PURE__ */ new Map()), r === "setter" && ((e = Object.create(e)).wrapped = !0), o.set(i.name, e), r === "accessor") {
    const { name: n } = i;
    return { set(a) {
      const l = t.get.call(this);
      t.set.call(this, a), this.requestUpdate(n, l, e, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(n, void 0, e, a), a;
    } };
  }
  if (r === "setter") {
    const { name: n } = i;
    return function(a) {
      const l = this[n];
      t.call(this, a), this.requestUpdate(n, l, e, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + r);
};
function f(e) {
  return (t, i) => typeof i == "object" ? Zt(e, t, i) : ((r, s, o) => {
    const n = s.hasOwnProperty(o);
    return s.constructor.createProperty(o, r), n ? Object.getOwnPropertyDescriptor(s, o) : void 0;
  })(e, t, i);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function m(e) {
  return f({ ...e, state: !0, attribute: !1 });
}
function Qt() {
  return "3.1.1";
}
function te(e) {
  const t = new Date(e).getTime(), r = Date.now() - t;
  if (r < 0) return "just now";
  const s = Math.floor(r / 6e4), o = Math.floor(s / 60), n = Math.floor(o / 24);
  return n > 0 ? `${n}d ${o % 24}h ago` : o > 0 ? `${o}h ${s % 60}m ago` : s > 0 ? `${s}m ago` : "just now";
}
function ee(e) {
  if (e < 60) return `${e}m`;
  const t = Math.floor(e / 60), i = e % 60;
  return i > 0 ? `${t}h ${i}m` : `${t}h`;
}
function ie(e) {
  const t = new Date(e), i = /* @__PURE__ */ new Date();
  let r = (i.getFullYear() - t.getFullYear()) * 12 + (i.getMonth() - t.getMonth());
  if (i.getDate() < t.getDate() && r--, r < 1) {
    const n = Math.floor(
      (i.getTime() - t.getTime()) / 864e5
    );
    return `${n} day${n !== 1 ? "s" : ""} old`;
  }
  if (r < 24)
    return `${r} month${r !== 1 ? "s" : ""} old`;
  const s = Math.floor(r / 12), o = r % 12;
  return o === 0 ? `${s} year${s !== 1 ? "s" : ""} old` : `${s}y ${o}m old`;
}
function se(e, t, i) {
  const r = {
    primary: null,
    sensors: [],
    timers: [],
    startTimerButton: null,
    binarySensors: [],
    selects: []
  }, s = i.find((a) => a.entity_id === e);
  if (!(s != null && s.device_id))
    return r.primary = t.states[e] ?? null, r;
  const o = s.device_id, n = i.filter(
    (a) => a.device_id === o && a.platform === "babybuddy"
  );
  for (const a of n) {
    const l = t.states[a.entity_id];
    if (!l) continue;
    const d = a.entity_id;
    d === e ? r.primary = l : d.startsWith("button.") && d.endsWith("_start_timer") ? r.startTimerButton = l : d.startsWith("sensor.") && l.attributes.timer_id != null ? r.timers.push(l) : d.startsWith("binary_sensor.") ? r.binarySensors.push(l) : d.startsWith("select.") ? r.selects.push(l) : d.startsWith("sensor.") && r.sensors.push(l);
  }
  return r;
}
function wt(e, t) {
  const i = e.split(".")[1] ?? e, r = t + "_";
  return i.startsWith(r) ? i.slice(r.length) : i;
}
function Et(e, t, i = "mdi:help-circle") {
  const r = t.find((s) => s.entity_id === e);
  return (r == null ? void 0 : r.original_icon) ?? i;
}
function re(e) {
  const t = {};
  for (const i of e) {
    if (i.platform !== "babybuddy" || !i.original_icon || !i.entity_id.startsWith("sensor.")) continue;
    const s = (i.entity_id.split(".")[1] ?? "").split("_");
    for (const o of s)
      o && !t[o] && (t[o] = i.original_icon);
  }
  return t;
}
function oe(e, t, i = "mdi:plus-circle") {
  const r = e.split("_");
  for (const s of r)
    if (s && t[s]) return t[s];
  return i;
}
function L(e) {
  return e.replace(/^add_/, "").replace(/^give_/, "").replace(/[-_]/g, " ").replace(/\b\w/g, (t) => t.toUpperCase());
}
var ne = Object.defineProperty, ae = Object.getOwnPropertyDescriptor, Z = (e, t, i, r) => {
  for (var s = r > 1 ? void 0 : r ? ae(t, i) : t, o = e.length - 1, n; o >= 0; o--)
    (n = e[o]) && (s = (r ? n(t, i, s) : n(s)) || s);
  return r && s && ne(t, i, s), s;
};
let H = class extends E {
  constructor() {
    super(...arguments), this.name = "", this.age = "", this.compact = !1;
  }
  render() {
    return c`
      <div class="header ${this.compact ? "compact" : ""}">
        ${this.picture ? c`<img class="avatar" src=${this.picture} alt=${this.name} />` : c`<div class="avatar placeholder">
              <ha-icon icon="mdi:baby-face-outline"></ha-icon>
            </div>`}
        <div class="info">
          <div class="name">${this.name}</div>
          <div class="age">${this.age}</div>
        </div>
      </div>
    `;
  }
  static get styles() {
    return F`
      :host {
        display: block;
      }
      .header {
        display: flex;
        align-items: center;
        gap: 12px;
        animation: fadeIn 0.3s ease;
      }
      .avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        object-fit: cover;
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }
      @media (hover: hover) {
        .avatar:hover {
          transform: scale(1.05);
        }
      }
      .placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--primary-color);
        color: var(--text-primary-color);
        --mdc-icon-size: 28px;
      }
      .info {
        min-width: 0;
        flex: 1;
      }
      .name {
        font-size: 1.1rem;
        font-weight: 500;
        color: var(--primary-text-color);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .age {
        font-size: 0.85rem;
        color: var(--secondary-text-color);
        margin-top: 1px;
      }
      .header.compact {
        gap: 8px;
        margin-bottom: 8px;
      }
      .header.compact .avatar {
        width: 32px;
        height: 32px;
      }
      .header.compact .placeholder {
        --mdc-icon-size: 20px;
      }
      .header.compact .name {
        font-size: 0.95rem;
      }
      .header.compact .age {
        font-size: 0.75rem;
      }
      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(-4px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
  }
};
Z([
  f()
], H.prototype, "name", 2);
Z([
  f()
], H.prototype, "age", 2);
Z([
  f()
], H.prototype, "picture", 2);
Z([
  f({ type: Boolean })
], H.prototype, "compact", 2);
H = Z([
  G("bb-child-header")
], H);
var le = Object.defineProperty, ce = Object.getOwnPropertyDescriptor, y = (e, t, i, r) => {
  for (var s = r > 1 ? void 0 : r ? ce(t, i) : t, o = e.length - 1, n; o >= 0; o--)
    (n = e[o]) && (s = (r ? n(t, i, s) : n(s)) || s);
  return r && s && le(t, i, s), s;
};
let g = class extends E {
  constructor() {
    super(...arguments), this.timers = [], this.startTimerButton = null, this.childEntityId = "", this._elapsed = {}, this._expandedTimerId = null, this._error = null, this._busy = !1, this._pendingStart = null, this._hiddenTimerIds = /* @__PURE__ */ new Set(), this._startExpanded = !1, this._editingTimerEntityId = null, this._editingName = "";
  }
  connectedCallback() {
    super.connectedCallback(), this._syncInterval(), this._boundDocClick = (e) => {
      e.composedPath().includes(this) || (this._editingTimerEntityId && (this._editingTimerEntityId = null), this._expandedTimerId && (this._expandedTimerId = null), this._startExpanded && (this._startExpanded = !1));
    }, document.addEventListener("click", this._boundDocClick), this._boundKeyDown = (e) => {
      e.key === "Escape" && (this._editingTimerEntityId && (this._editingTimerEntityId = null), this._expandedTimerId && (this._expandedTimerId = null), this._startExpanded && (this._startExpanded = !1));
    }, document.addEventListener("keydown", this._boundKeyDown);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._interval && (clearInterval(this._interval), this._interval = void 0), this._errorTimeout && clearTimeout(this._errorTimeout), this._boundDocClick && document.removeEventListener("click", this._boundDocClick), this._boundKeyDown && document.removeEventListener("keydown", this._boundKeyDown);
  }
  willUpdate(e) {
    if (e.has("timers")) {
      this._syncInterval(), this._pendingStart && (this._pendingStart = null);
      const t = new Set(this.timers.map((i) => i.entity_id));
      for (const i of this._hiddenTimerIds)
        t.has(i) || this._hiddenTimerIds.delete(i);
      this._hiddenTimerIds.size > 0 && (this._hiddenTimerIds = new Set(this._hiddenTimerIds));
    }
  }
  _syncInterval() {
    this.timers.filter(
      (t) => !this._hiddenTimerIds.has(t.entity_id)
    ).length > 0 || this._pendingStart ? this._interval || (this._tick(), this._interval = setInterval(() => this._tick(), 1e3)) : this._interval && (clearInterval(this._interval), this._interval = void 0);
  }
  _tick() {
    const e = {};
    for (const t of this.timers) {
      const i = t.state;
      if (!i || i === "unavailable" || i === "unknown") {
        e[t.entity_id] = "0:00:00";
        continue;
      }
      const r = Date.now() - new Date(i).getTime();
      if (r < 0) {
        e[t.entity_id] = "0:00:00";
        continue;
      }
      const s = Math.floor(r / 36e5), o = Math.floor(r % 36e5 / 6e4), n = Math.floor(r % 6e4 / 1e3);
      e[t.entity_id] = `${s}:${String(o).padStart(2, "0")}:${String(n).padStart(2, "0")}`;
    }
    this._elapsed = e;
  }
  _getTimerActions() {
    var t, i;
    const e = (i = (t = this.hass) == null ? void 0 : t.services) == null ? void 0 : i.babybuddy;
    return e ? Object.entries(e).filter(([, r]) => r.fields && "timer" in r.fields).map(([r, s]) => ({
      key: r,
      label: L(r)
    })) : [];
  }
  _selectAction(e, t) {
    const i = t.attributes.timer_id;
    i != null && (this._expandedTimerId = null, this.dispatchEvent(
      new CustomEvent("bb-timer-stop", {
        detail: { action: e, timerId: i },
        bubbles: !0,
        composed: !0
      })
    ));
  }
  _showError(e) {
    this._error = e, this._errorTimeout && clearTimeout(this._errorTimeout), this._errorTimeout = setTimeout(() => {
      this._error = null;
    }, 5e3);
  }
  async _discardTimer(e) {
    const t = e.attributes.timer_id;
    if (t != null) {
      this._expandedTimerId = null, this._hiddenTimerIds.add(e.entity_id), this._hiddenTimerIds = new Set(this._hiddenTimerIds);
      try {
        await this.hass.callService("babybuddy", "stop_timer", {
          timer_id: t
        });
      } catch (i) {
        this._hiddenTimerIds.delete(e.entity_id), this._hiddenTimerIds = new Set(this._hiddenTimerIds), this._showError(
          i instanceof Error ? i.message : "Failed to stop timer"
        );
      }
    }
  }
  async _startTimer(e) {
    if (!this.childEntityId || this._busy) return;
    this._busy = !0, this._startExpanded = !1;
    const t = e || "Timer";
    try {
      const i = { child: this.childEntityId };
      e && (i.name = e), await this.hass.callService("babybuddy", "start_timer", i), this._pendingStart = t;
    } catch (i) {
      this._showError(
        i instanceof Error ? i.message : "Failed to start timer"
      );
    } finally {
      this._busy = !1;
    }
  }
  _beginEdit(e, t) {
    if (t.stopPropagation(), this._editingTimerEntityId && this._editingTimerEntityId !== e.entity_id) {
      const i = this.timers.find((r) => r.entity_id === this._editingTimerEntityId);
      i && this._commitRename(i);
    }
    this._editingTimerEntityId = e.entity_id, this._editingName = e.attributes.timer_name ?? "Timer";
  }
  async _commitRename(e) {
    const t = e.attributes.timer_id, i = this._editingName.trim();
    if (this._editingTimerEntityId = null, !(t == null || !i))
      try {
        await this.hass.callService("babybuddy", "rename_timer", {
          timer_id: t,
          name: i
        });
      } catch (r) {
        this._showError(
          r instanceof Error ? r.message : "Failed to rename timer"
        );
      }
  }
  _cancelEdit() {
    this._editingTimerEntityId = null;
  }
  render() {
    const e = this.timers.filter(
      (t) => !this._hiddenTimerIds.has(t.entity_id)
    );
    return c`
      ${e.length > 0 ? e.map((t) => this._renderTimer(t)) : h}
      ${this._pendingStart ? c`
            <div class="timer active pending">
              <div class="timer-face">
                <ha-icon icon="mdi:timer" class="icon"></ha-icon>
                <span class="label">${this._pendingStart}</span>
                <span class="elapsed">0:00:00</span>
              </div>
            </div>
          ` : h}
      ${this._renderStartArea()}
      ${this._error ? c`<div class="error">${this._error}</div>` : h}
    `;
  }
  _renderStartArea() {
    if (!this.childEntityId) return h;
    const e = this._startExpanded, t = this._getTimerActions();
    return c`
      <div
        class="elastic-shell ${e ? "open" : ""}"
        @click=${(i) => i.stopPropagation()}
      >
        <button
          class="elastic-trigger ${e ? "shrunk" : ""}"
          ?disabled=${this._busy}
          title=${e ? "Cancel" : ""}
          @click=${(i) => {
      i.stopPropagation(), e ? this._startExpanded = !1 : this._startExpanded = !0;
    }}
        >
          <ha-icon
            icon=${e ? "mdi:close-thick" : "mdi:timer-plus"}
          ></ha-icon>
          <span>${this._busy ? "Starting..." : "Start Timer"}</span>
        </button>
        <div class="elastic-opts ${e ? "open" : ""}">
          ${e ? c`
                ${t.map(
      (i) => c`
                    <button
                      class="elastic-opt"
                      @click=${() => this._startTimer(i.label)}
                    >
                      ${i.label}
                    </button>
                  `
    )}
                <button
                  class="elastic-opt unnamed"
                  @click=${() => this._startTimer()}
                  title="Start unnamed timer"
                >
                  <ha-icon icon="mdi:timer-outline"></ha-icon>
                </button>
              ` : h}
        </div>
      </div>
    `;
  }
  _renderTimer(e) {
    const t = this._expandedTimerId === e.entity_id, i = e.attributes.timer_name ?? e.attributes.friendly_name ?? "Timer", r = this._elapsed[e.entity_id] ?? "0:00:00", s = this._editingTimerEntityId === e.entity_id, o = this._getTimerActions();
    return c`
      <div
        class="timer active"
        @click=${(n) => n.stopPropagation()}
      >
        <div class="timer-face ${t ? "hidden" : ""}">
          <ha-icon icon="mdi:timer" class="icon"></ha-icon>
          ${s ? c`
                <input
                  class="rename-input"
                  .value=${this._editingName}
                  @input=${(n) => {
      this._editingName = n.target.value;
    }}
                  @keydown=${(n) => {
      n.key === "Enter" && this._commitRename(e), n.key === "Escape" && this._cancelEdit();
    }}
                  @blur=${() => {
      this._editingTimerEntityId === e.entity_id && this._commitRename(e);
    }}
                  @click=${(n) => n.stopPropagation()}
                />
              ` : c`
                <span
                  class="label editable"
                  @click=${(n) => this._beginEdit(e, n)}
                  title="Click to rename"
                >${i}</span>
              `}
          <span class="elapsed">${r}</span>
          <button
            class="toggle"
            title="Stop timer"
            @click=${(n) => {
      n.stopPropagation(), this._editingTimerEntityId = null, this._startExpanded = !1, this._expandedTimerId = e.entity_id;
    }}
          >
            <ha-icon icon="mdi:stop"></ha-icon>
          </button>
        </div>
        <div class="timer-opts ${t ? "open" : ""}">
          <button
            class="elastic-opt discard"
            title="Discard timer"
            @click=${() => this._discardTimer(e)}
          >
            <ha-icon icon="mdi:close-thick"></ha-icon>
          </button>
          ${o.map(
      (n) => c`
              <button
                class="elastic-opt"
                @click=${() => this._selectAction(n.key, e)}
              >
                ${n.label}
              </button>
            `
    )}
        </div>
      </div>
    `;
  }
  updated() {
    var e, t;
    if (this._editingTimerEntityId) {
      const i = (e = this.shadowRoot) == null ? void 0 : e.querySelector(
        ".rename-input"
      );
      i && ((t = this.shadowRoot) == null ? void 0 : t.activeElement) !== i && (i.focus(), i.select());
    }
  }
  static get styles() {
    return F`
      :host {
        display: block;
      }
      .timer {
        display: flex;
        align-items: stretch;
        gap: 0;
        padding: 0;
        border-radius: 12px;
        background: var(--card-background-color, var(--ha-card-background));
        border: 1px solid var(--divider-color);
        margin-bottom: 8px;
        overflow: hidden;
        transition: all 0.3s ease;
      }
      .timer.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }
      .timer.active .icon {
        animation: pulse 1.5s ease-in-out infinite;
      }
      .timer.pending {
        opacity: 0.7;
      }
      .label {
        font-weight: 500;
        font-size: 0.9rem;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .label.editable {
        cursor: pointer;
        border-bottom: 1px dashed rgba(255, 255, 255, 0.4);
      }
      .rename-input {
        font-weight: 500;
        font-size: 0.9rem;
        font-family: inherit;
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 6px;
        color: inherit;
        padding: 2px 6px;
        min-width: 0;
        width: 120px;
        outline: none;
      }
      .elapsed {
        flex: 1;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-size: 1.1rem;
        font-weight: 600;
      }
      .toggle {
        background: none;
        border: none;
        cursor: pointer;
        color: inherit;
        padding: 4px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        --mdc-icon-size: 24px;
      }
      @media (hover: hover) {
        .toggle:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      }
      .timer-face {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        min-width: 0;
        padding: 8px 12px;
        overflow: hidden;
        transition: flex 0.3s ease, opacity 0.2s ease, padding 0.3s ease;
      }
      .timer-face.hidden {
        flex: 0;
        opacity: 0;
        padding: 8px 0;
        pointer-events: none;
      }
      .timer-opts {
        display: flex;
        align-items: stretch;
        flex: 0;
        overflow: hidden;
        transition: flex 0.3s ease, opacity 0.2s ease;
        opacity: 0;
      }
      .timer-opts.open {
        flex: 1;
        opacity: 1;
      }
      .timer-opts .elastic-opt {
        border-left-color: rgba(255, 255, 255, 0.15);
        color: inherit;
      }
      @media (hover: hover) {
        .timer-opts .elastic-opt:hover {
          background: rgba(255, 255, 255, 0.15);
          color: inherit;
        }
      }
      .elastic-opt.discard {
        flex: 0 0 42px;
        padding: 8px;
        border-left: none;
        --mdc-icon-size: 18px;
      }
      .timer-opts .elastic-opt.discard {
        color: var(--error-color, #db4437);
        background: rgba(255, 255, 255, 0.15);
      }
      @media (hover: hover) {
        .timer-opts .elastic-opt.discard:hover {
          background: var(--error-color, #db4437);
          color: var(--text-primary-color);
        }
      }
      .elastic-shell {
        display: flex;
        gap: 0;
        border-radius: 12px;
        overflow: hidden;
        border: 1px dashed color-mix(in srgb, var(--primary-color) 40%, transparent);
        margin-bottom: 8px;
        transition: all 0.3s ease;
      }
      .elastic-shell.open {
        border-style: solid;
        border-color: var(--primary-color);
      }
      .elastic-trigger {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 10px;
        border: none;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.85rem;
        font-family: inherit;
        font-weight: 500;
        transition: all 0.3s ease;
        flex: 1;
        white-space: nowrap;
        --mdc-icon-size: 18px;
      }
      @media (hover: hover) {
        .elastic-trigger:hover {
          color: var(--primary-color);
        }
      }
      .elastic-trigger.shrunk {
        flex: 0 0 42px;
        padding: 8px;
        background: none;
        color: var(--error-color, #db4437);
        border-radius: 0;
        --mdc-icon-size: 18px;
      }
      @media (hover: hover) {
        .elastic-trigger.shrunk:hover {
          background: var(--error-color, #db4437);
          color: var(--text-primary-color);
        }
      }
      .elastic-trigger.shrunk span {
        display: none;
      }
      .elastic-trigger:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .elastic-opts {
        display: flex;
        flex: 0;
        overflow: hidden;
        transition: flex 0.3s ease;
      }
      .elastic-opts.open {
        flex: 1;
      }
      .elastic-opt {
        flex: 1;
        padding: 8px 4px;
        border: none;
        border-left: 1px solid var(--divider-color);
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.78rem;
        font-family: inherit;
        font-weight: 500;
        transition: all 0.15s ease;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        --mdc-icon-size: 16px;
      }
      @media (hover: hover) {
        .elastic-opt:hover {
          background: var(--primary-color);
          color: var(--text-primary-color);
        }
      }
      .elastic-opt.unnamed {
        flex: 0 0 42px;
      }
      .error {
        padding: 4px 12px;
        font-size: 0.8rem;
        color: var(--error-color, #db4437);
      }
      @keyframes pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }
    `;
  }
};
y([
  f({ attribute: !1 })
], g.prototype, "hass", 2);
y([
  f({ attribute: !1 })
], g.prototype, "timers", 2);
y([
  f({ attribute: !1 })
], g.prototype, "startTimerButton", 2);
y([
  f({ attribute: !1 })
], g.prototype, "childEntityId", 2);
y([
  m()
], g.prototype, "_elapsed", 2);
y([
  m()
], g.prototype, "_expandedTimerId", 2);
y([
  m()
], g.prototype, "_error", 2);
y([
  m()
], g.prototype, "_busy", 2);
y([
  m()
], g.prototype, "_pendingStart", 2);
y([
  m()
], g.prototype, "_hiddenTimerIds", 2);
y([
  m()
], g.prototype, "_startExpanded", 2);
y([
  m()
], g.prototype, "_editingTimerEntityId", 2);
y([
  m()
], g.prototype, "_editingName", 2);
g = y([
  G("bb-timer-bar")
], g);
var de = Object.defineProperty, he = Object.getOwnPropertyDescriptor, $ = (e, t, i, r) => {
  for (var s = r > 1 ? void 0 : r ? he(t, i) : t, o = e.length - 1, n; o >= 0; o--)
    (n = e[o]) && (s = (r ? n(t, i, s) : n(s)) || s);
  return r && s && de(t, i, s), s;
};
const T = "__other__", pe = /* @__PURE__ */ new Set([
  "device_class",
  "state_class",
  "unit_of_measurement",
  "friendly_name",
  "icon",
  "bb_group",
  "bb_color",
  "entity_picture",
  "supported_features",
  "attribution",
  "timer_id",
  "timer_name"
]);
let _ = class extends E {
  constructor() {
    super(...arguments), this.sensors = [], this.binarySensors = [], this.entityRegistry = [], this.childPrefix = "", this.sensorGroups = [], this.compact = !1, this._collapsed = {}, this._expandedRows = /* @__PURE__ */ new Set(), this._pendingDelete = null, this._deleteError = null, this._defaultsApplied = !1, this._prevChildPrefix = "", this._cachedGroups = [], this._groupsDirty = !0;
  }
  get _storageKey() {
    return this.childPrefix ? `${_._STORAGE_KEY_PREFIX}-${this.childPrefix}` : _._STORAGE_KEY_PREFIX;
  }
  willUpdate(e) {
    e.has("childPrefix") && this.childPrefix !== this._prevChildPrefix && (this._prevChildPrefix = this.childPrefix, this._defaultsApplied = !1), this._defaultsApplied || this._applyDefaults(), (e.has("sensors") || e.has("binarySensors") || e.has("sensorGroups") || e.has("_collapsed")) && (this._groupsDirty = !0);
  }
  _buildRow(e) {
    const t = wt(e.entity_id, this.childPrefix), i = Et(
      e.entity_id,
      this.entityRegistry,
      "mdi:clock-outline"
    ), r = L(t), s = e.attributes.device_class;
    let o;
    s === "timestamp" ? o = te(e.state) : s === "duration" && !isNaN(Number(e.state)) ? o = ee(Math.round(Number(e.state))) : o = this.hass.formatEntityState(e);
    const n = e.attributes.bb_color ?? "";
    return { icon: i, label: r, value: o, color: n, entityId: e.entity_id };
  }
  _applyDefaults() {
    if (this._defaultsApplied) return;
    try {
      const t = localStorage.getItem(this._storageKey);
      if (t) {
        this._collapsed = JSON.parse(t), this._defaultsApplied = !0;
        return;
      }
    } catch {
    }
    const e = {};
    for (const t of this.sensorGroups)
      e[t.id] = t.default_collapsed;
    e[T] = !0, this._collapsed = e, this._defaultsApplied = !0;
  }
  _buildGroups() {
    if (!this._groupsDirty) return this._cachedGroups;
    this._groupsDirty = !1;
    const e = /* @__PURE__ */ new Map();
    for (const s of this.sensorGroups)
      e.set(s.id, s);
    const t = {};
    for (const s of this.sensorGroups) t[s.id] = [];
    t[T] = [];
    for (const s of this.sensors) {
      if (!s.state || s.state === "unknown" || s.state === "unavailable")
        continue;
      const o = s.attributes.bb_group ?? "";
      o && t[o] ? t[o].push(this._buildRow(s)) : t[T].push(this._buildRow(s));
    }
    for (const s of this.binarySensors) {
      if (s.state === "unavailable") continue;
      const o = wt(s.entity_id, this.childPrefix), n = Et(
        s.entity_id,
        this.entityRegistry,
        s.state === "on" ? "mdi:check-circle" : "mdi:circle-outline"
      ), a = L(o), l = s.state === "on" ? "Yes" : "No", d = s.attributes.bb_color ?? "", p = s.attributes.bb_group ?? "", u = p && t[p] ? p : T;
      t[u].push({
        icon: n,
        label: a,
        value: l,
        color: d,
        entityId: s.entity_id
      });
    }
    const i = [...this.sensorGroups].sort((s, o) => s.order - o.order), r = [];
    for (const s of i)
      t[s.id].length > 0 && r.push({
        id: s.id,
        title: s.title,
        icon: s.icon,
        color: s.color ?? "",
        rows: t[s.id],
        collapsed: this._collapsed[s.id] ?? s.default_collapsed
      });
    return t[T].length > 0 && r.push({
      id: T,
      title: "Other",
      icon: "mdi:information-outline",
      color: "",
      rows: t[T],
      collapsed: this._collapsed[T] ?? !0
    }), this._cachedGroups = r, r;
  }
  _toggleGroup(e) {
    this._collapsed = {
      ...this._collapsed,
      [e]: !this._collapsed[e]
    };
    try {
      localStorage.setItem(
        this._storageKey,
        JSON.stringify(this._collapsed)
      );
    } catch {
    }
  }
  _toggleRow(e) {
    const t = new Set(this._expandedRows);
    t.has(e) ? t.delete(e) : t.add(e), this._expandedRows = t;
  }
  _bbAttributes(e) {
    const t = this.hass.states[e];
    return t ? Object.entries(t.attributes).filter(
      ([i, r]) => !pe.has(i) && r != null && r !== ""
    ) : [];
  }
  static _formatKey(e) {
    return e.replace(/_/g, " ").replace(/\b\w/g, (t) => t.toUpperCase());
  }
  get _canDelete() {
    var e, t;
    return !!((t = (e = this.hass.services) == null ? void 0 : e.babybuddy) != null && t.delete_last_entry);
  }
  _hasEntryId(e) {
    var i;
    const t = this.hass.states[e];
    return ((i = t == null ? void 0 : t.attributes) == null ? void 0 : i.id) != null;
  }
  _confirmDelete(e) {
    this._pendingDelete = e;
  }
  _cancelDelete() {
    this._pendingDelete = null;
  }
  async _executeDelete(e) {
    this._pendingDelete = null;
    try {
      await this.hass.callService("babybuddy", "delete_last_entry", {
        entity_id: e
      });
    } catch (t) {
      this._deleteError = t instanceof Error ? t.message : "Failed to delete entry", this._deleteErrorTimeout && clearTimeout(this._deleteErrorTimeout), this._deleteErrorTimeout = setTimeout(() => {
        this._deleteError = null;
      }, 5e3);
    }
  }
  render() {
    const e = this._buildGroups();
    return e.length === 0 ? h : c`
      <div class="sections ${this.compact ? "compact" : ""}">
        ${e.map((t) => this._renderGroup(t))}
      </div>
    `;
  }
  _renderGroup(e) {
    return c`
      <div class="group">
        <button
          class="group-header"
          @click=${() => this._toggleGroup(e.id)}
        >
          <ha-icon icon=${e.icon} class="group-icon"></ha-icon>
          <span class="group-title">${e.title}</span>
          <span class="group-count">${e.rows.length}</span>
          <ha-icon
            icon=${e.collapsed ? "mdi:chevron-down" : "mdi:chevron-up"}
            class="group-toggle"
          ></ha-icon>
        </button>
        ${e.collapsed ? h : c`
              <div class="group-body">
                ${e.rows.map((t) => this._renderRow(t))}
              </div>
            `}
      </div>
    `;
  }
  _renderRow(e) {
    const t = this._expandedRows.has(e.entityId), i = t ? this._bbAttributes(e.entityId) : [];
    return c`
      <div class="row-block">
        ${this._renderRowHeader(e, t)}
        ${t && i.length > 0 ? this._renderRowDetail(i) : h}
        ${t && this._canDelete && this._hasEntryId(e.entityId) ? this._renderDeleteAction(e.entityId) : h}
      </div>
    `;
  }
  _renderRowHeader(e, t) {
    return c`
      <div
        class="row ${t ? "expanded" : ""}"
        role="button"
        tabindex="0"
        aria-expanded=${t}
        @click=${() => this._toggleRow(e.entityId)}
        @keydown=${(i) => {
      (i.key === "Enter" || i.key === " ") && (i.preventDefault(), this._toggleRow(e.entityId));
    }}
      >
        <ha-icon
          icon=${e.icon}
          class="row-icon"
          style=${e.color ? `color: ${e.color}` : ""}
        ></ha-icon>
        <span class="row-label">${e.label}</span>
        <span class="row-value">${e.value}</span>
        <ha-icon
          icon=${t ? "mdi:chevron-up" : "mdi:chevron-down"}
          class="row-toggle"
        ></ha-icon>
      </div>
    `;
  }
  _renderRowDetail(e) {
    return c`
      <div class="row-detail">
        ${e.map(
      ([t, i]) => c`
            <div class="detail-item">
              <span class="detail-key">${_._formatKey(t)}</span>
              <span class="detail-val">${i}</span>
            </div>
          `
    )}
      </div>
    `;
  }
  _renderDeleteAction(e) {
    const t = this._pendingDelete === e;
    return c`
      <div class="row-actions">
        <button
          class="delete-btn ${t ? "confirming" : ""}"
          @click=${(i) => {
      i.stopPropagation(), t || this._confirmDelete(e);
    }}
        >
          <span class="delete-default">
            <ha-icon icon="mdi:delete-outline"></ha-icon>
            Delete
          </span>
          <span class="delete-confirm">
            <span class="confirm-label">Delete?</span>
            <span
              class="confirm-yes"
              @click=${(i) => {
      i.stopPropagation(), this._executeDelete(e);
    }}
            >Yes</span>
            <span
              class="confirm-cancel"
              @click=${(i) => {
      i.stopPropagation(), this._cancelDelete();
    }}
            >Cancel</span>
          </span>
        </button>
        ${this._deleteError && this._pendingDelete === null ? c`<div class="delete-error">${this._deleteError}</div>` : h}
      </div>
    `;
  }
  static get styles() {
    return F`
      :host {
        display: block;
      }
      .sections {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      /* ── Group chrome ── */
      .group {
        border-radius: 12px;
        overflow: hidden;
        background: var(--secondary-background-color);
      }
      .group-header {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
        padding: 8px 12px;
        border: none;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-family: inherit;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        outline: none;
        --mdc-icon-size: 16px;
      }
      @media (hover: hover) {
        .group-header:hover {
          background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
        }
      }
      .group-header:focus-visible {
        box-shadow: inset 0 0 0 2px var(--primary-color);
      }
      .group-icon {
        color: var(--secondary-text-color);
        flex-shrink: 0;
      }
      .group-title {
        flex: 1;
        text-align: left;
      }
      .group-count {
        color: var(--secondary-text-color);
        font-size: 0.72rem;
        font-weight: 400;
        background: var(--card-background-color, var(--ha-card-background));
        padding: 1px 7px;
        border-radius: 10px;
      }
      .group-toggle {
        color: var(--secondary-text-color);
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }
      .group-body {
        padding: 0 4px 4px;
      }

      /* ── Row header ── */
      .row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 8px;
        border-radius: 8px;
        font-size: 0.85rem;
        transition: background 0.15s ease;
        --mdc-icon-size: 18px;
      }
      @media (hover: hover) {
        .row:hover {
          background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.05);
        }
      }
      .row-icon {
        flex-shrink: 0;
        color: var(--secondary-text-color);
      }
      .row-label {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--primary-text-color);
      }
      .row-value {
        flex-shrink: 0;
        font-weight: 500;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
        text-align: right;
      }
      .row-toggle {
        flex-shrink: 0;
        color: var(--disabled-text-color, #999);
        --mdc-icon-size: 14px;
      }
      .row.expanded {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.06);
      }

      /* ── Expanded detail key/value pairs ── */
      .row-detail {
        padding: 2px 8px 6px 44px;
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .detail-item {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-size: 0.78rem;
        line-height: 1.4;
      }
      .detail-key {
        color: var(--secondary-text-color);
        white-space: nowrap;
      }
      .detail-val {
        color: var(--primary-text-color);
        text-align: right;
        word-break: break-word;
        min-width: 0;
      }

      /* ── Delete action (lives outside .row-detail, centered) ── */
      .row-actions {
        padding: 0 8px 4px;
      }
      .delete-btn {
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        margin-top: 4px;
        padding: 6px 8px;
        border: none;
        border-radius: 6px;
        background: rgba(var(--rgb-error-color, 219, 68, 55), 0.1);
        color: var(--error-color, #db4437);
        font-family: inherit;
        font-size: 0.75rem;
        cursor: pointer;
        --mdc-icon-size: 14px;
      }
      @media (hover: hover) {
        .delete-btn:hover {
          background: rgba(var(--rgb-error-color, 219, 68, 55), 0.18);
        }
      }
      .delete-btn:focus-visible {
        box-shadow: 0 0 0 2px var(--error-color, #db4437);
        outline: none;
      }
      .delete-btn.confirming {
        background: rgba(var(--rgb-error-color, 219, 68, 55), 0.15);
        cursor: default;
      }
      @media (hover: hover) {
        .delete-btn.confirming:hover {
          background: rgba(var(--rgb-error-color, 219, 68, 55), 0.15);
        }
      }

      .delete-default {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
      }
      .delete-btn.confirming .delete-default {
        visibility: hidden;
      }

      .delete-confirm {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        opacity: 0;
        pointer-events: none;
      }
      .delete-btn.confirming .delete-confirm {
        opacity: 1;
        pointer-events: auto;
      }

      .confirm-yes,
      .confirm-cancel {
        min-width: 48px;
        padding: 2px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.75rem;
        text-align: center;
      }
      .confirm-yes {
        background: var(--error-color, #db4437);
        color: #fff;
      }
      @media (hover: hover) {
        .confirm-yes:hover {
          opacity: 0.85;
        }
      }
      .confirm-cancel {
        background: var(--card-background-color, var(--ha-card-background));
        color: var(--primary-text-color);
      }
      @media (hover: hover) {
        .confirm-cancel:hover {
          opacity: 0.8;
        }
      }

      .delete-error {
        margin-top: 4px;
        padding: 4px 8px;
        font-size: 0.75rem;
        color: var(--error-color, #db4437);
      }

      /* ── Compact overrides ── */
      .sections.compact .group-header {
        padding: 6px 10px;
        font-size: 0.72rem;
        --mdc-icon-size: 14px;
      }
      .sections.compact .row {
        padding: 4px 8px;
        font-size: 0.78rem;
        --mdc-icon-size: 16px;
      }
    `;
  }
};
_._STORAGE_KEY_PREFIX = "bb-card-collapsed";
$([
  f({ attribute: !1 })
], _.prototype, "hass", 2);
$([
  f({ attribute: !1 })
], _.prototype, "sensors", 2);
$([
  f({ attribute: !1 })
], _.prototype, "binarySensors", 2);
$([
  f({ attribute: !1 })
], _.prototype, "entityRegistry", 2);
$([
  f()
], _.prototype, "childPrefix", 2);
$([
  f({ attribute: !1 })
], _.prototype, "sensorGroups", 2);
$([
  f({ type: Boolean })
], _.prototype, "compact", 2);
$([
  m()
], _.prototype, "_collapsed", 2);
$([
  m()
], _.prototype, "_expandedRows", 2);
$([
  m()
], _.prototype, "_pendingDelete", 2);
$([
  m()
], _.prototype, "_deleteError", 2);
_ = $([
  G("bb-activity-chips")
], _);
var ue = Object.defineProperty, fe = Object.getOwnPropertyDescriptor, B = (e, t, i, r) => {
  for (var s = r > 1 ? void 0 : r ? fe(t, i) : t, o = e.length - 1, n; o >= 0; o--)
    (n = e[o]) && (s = (r ? n(t, i, s) : n(s)) || s);
  return r && s && ue(t, i, s), s;
};
const me = /* @__PURE__ */ new Set([
  "delete_last_entry",
  "add_child",
  "start_timer",
  "stop_timer"
]), _e = [
  "feeding",
  "diaper",
  "change",
  "sleep",
  "tummy",
  "pumping",
  "medication"
];
function At(e) {
  for (const [t, i] of _e.entries())
    if (e.includes(i)) return t;
  return 100;
}
let O = class extends E {
  constructor() {
    super(...arguments), this.entityRegistry = [], this.compact = !1, this._showMore = !1;
  }
  _getAvailableActions() {
    var i, r;
    const e = (r = (i = this.hass) == null ? void 0 : i.services) == null ? void 0 : r.babybuddy;
    if (!e) return [];
    const t = re(this.entityRegistry);
    return Object.keys(e).filter((s) => !me.has(s) && !s.startsWith("_")).map((s) => ({
      key: s,
      label: e[s].name ?? L(s),
      icon: oe(s, t)
    })).sort((s, o) => At(s.key) - At(o.key));
  }
  _fireAction(e) {
    this.dispatchEvent(
      new CustomEvent("bb-action", {
        detail: { action: e },
        bubbles: !0,
        composed: !0
      })
    );
  }
  render() {
    const e = this._getAvailableActions(), t = this._showMore ? e : e.slice(0, 4);
    return c`
      <div class="actions ${this.compact ? "compact" : ""}">
        ${t.map(
      (i) => c`
            <button
              class="action-btn"
              title=${i.label}
              @click=${() => this._fireAction(i.key)}
            >
              <ha-icon icon=${i.icon}></ha-icon>
              ${this.compact ? h : c`<span>${i.label}</span>`}
            </button>
          `
    )}
        ${e.length > 4 && !this._showMore ? c`
              <button
                class="action-btn more"
                title="More actions"
                @click=${() => this._showMore = !0}
              >
                <ha-icon icon="mdi:dots-horizontal"></ha-icon>
                ${this.compact ? h : c`<span>More</span>`}
              </button>
            ` : e.length > 4 && this._showMore ? c`
                <button
                  class="action-btn more"
                  title="Show less"
                  @click=${() => this._showMore = !1}
                >
                  <ha-icon icon="mdi:chevron-up"></ha-icon>
                  ${this.compact ? h : c`<span>Less</span>`}
                </button>
              ` : h}
      </div>
    `;
  }
  static get styles() {
    return F`
      :host {
        display: block;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .action-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 6px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 18px;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.8rem;
        font-family: inherit;
        transition: all 0.2s ease;
        --mdc-icon-size: 18px;
        outline: none;
      }
      @media (hover: hover) {
        .action-btn:hover {
          background: var(--primary-color);
          color: var(--text-primary-color);
          border-color: var(--primary-color);
        }
      }
      .action-btn:focus-visible {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px var(--primary-color);
      }
      .action-btn:active {
        transform: scale(0.96);
      }
      .action-btn.more {
        border-style: dashed;
      }
      .actions.compact {
        gap: 4px;
      }
      .actions.compact .action-btn {
        padding: 6px;
        border-radius: 50%;
        --mdc-icon-size: 16px;
      }
    `;
  }
};
B([
  f({ attribute: !1 })
], O.prototype, "hass", 2);
B([
  f({ attribute: !1 })
], O.prototype, "childEntity", 2);
B([
  f({ attribute: !1 })
], O.prototype, "entityRegistry", 2);
B([
  f({ type: Boolean })
], O.prototype, "compact", 2);
B([
  m()
], O.prototype, "_showMore", 2);
O = B([
  G("bb-action-buttons")
], O);
var be = Object.defineProperty, ge = Object.getOwnPropertyDescriptor, A = (e, t, i, r) => {
  for (var s = r > 1 ? void 0 : r ? ge(t, i) : t, o = e.length - 1, n; o >= 0; o--)
    (n = e[o]) && (s = (r ? n(t, i, s) : n(s)) || s);
  return r && s && be(t, i, s), s;
};
let w = class extends E {
  constructor() {
    super(...arguments), this.action = "", this.timers = [], this.selects = [], this._formData = {}, this._submitting = !1, this._error = null, this._initialTimerApplied = !1, this._defaultsApplied = !1;
  }
  _getServiceFields() {
    var i, r, s;
    const e = (s = (r = (i = this.hass) == null ? void 0 : i.services) == null ? void 0 : r.babybuddy) == null ? void 0 : s[this.action];
    if (!(e != null && e.fields)) return {};
    const t = { ...e.fields };
    for (const [o, n] of Object.entries(t)) {
      const a = n.selector;
      if (!(a != null && a.select)) continue;
      const l = a.select;
      if (l.options && l.options.length > 0)
        continue;
      const d = this.selects.find((p) => {
        const u = p.entity_id;
        return u.includes(o) || u.endsWith(`_${o}`);
      });
      if (d) {
        const p = d.attributes.options;
        p && (t[o] = {
          ...n,
          selector: {
            select: { ...l, options: p }
          }
        });
      }
    }
    return t;
  }
  connectedCallback() {
    super.connectedCallback(), this._onKeyDown = this._onKeyDown.bind(this), window.addEventListener("keydown", this._onKeyDown), this._initialTimerApplied = !1, this._defaultsApplied = !1;
  }
  updated(e) {
    var r, s, o, n;
    super.updated(e);
    const t = (n = (o = (s = (r = this.hass) == null ? void 0 : r.services) == null ? void 0 : s.babybuddy) == null ? void 0 : o[this.action]) == null ? void 0 : n.fields, i = t != null && "timer" in t;
    if (!i && this._formData._selected_timer != null) {
      this._formData = { ...this._formData, _selected_timer: void 0 };
      return;
    }
    if (!this._initialTimerApplied && this.initialTimerId != null && i && this.timers.find(
      (l) => l.attributes.timer_id === this.initialTimerId
    ) && (this._formData = {
      ...this._formData,
      _selected_timer: this.initialTimerId
    }, this._initialTimerApplied = !0), !this._defaultsApplied && this.action && t) {
      this._defaultsApplied = !0;
      const a = /* @__PURE__ */ new Date(), l = String(a.getHours()).padStart(2, "0"), d = String(a.getMinutes()).padStart(2, "0"), p = `${l}:${d}`, u = `${a.getFullYear()}-${String(a.getMonth() + 1).padStart(2, "0")}-${String(a.getDate()).padStart(2, "0")}`, b = {};
      for (const [x, M] of Object.entries(t)) {
        const st = M, z = st.selector;
        st.default === "now" && (z == null ? void 0 : z.time) != null ? b[x] = p : st.default === "today" && (z == null ? void 0 : z.date) != null && (b[x] = u);
      }
      Object.keys(b).length > 0 && (this._formData = { ...b, ...this._formData });
    }
  }
  disconnectedCallback() {
    super.disconnectedCallback(), window.removeEventListener("keydown", this._onKeyDown);
  }
  _onKeyDown(e) {
    e.key === "Escape" && this._close();
  }
  _close() {
    this.dispatchEvent(
      new CustomEvent("bb-dialog-close", {
        bubbles: !0,
        composed: !0
      })
    );
  }
  _updateField(e, t) {
    this._formData = { ...this._formData, [e]: t };
  }
  _activeExclusionGroups(e) {
    const t = /* @__PURE__ */ new Set(), i = e.timer, r = i == null ? void 0 : i.exclusion_group;
    return this._formData._selected_timer != null && r && t.add(r), t;
  }
  _isFieldHidden(e, t, i) {
    if (e === "entity_id" || t.hidden_in_card === !0) return !0;
    const r = t.exclusion_group;
    if (r && i.has(r)) return !0;
    const s = t.hidden_when_group;
    return !!(s && i.has(s));
  }
  _textColorFor(e) {
    let t = e.replace("#", "");
    if (/^[0-9a-f]{3}$/i.test(t) && (t = t[0] + t[0] + t[1] + t[1] + t[2] + t[2]), !/^[0-9a-f]{6}$/i.test(t)) return "#000";
    const i = parseInt(t.substring(0, 2), 16) / 255, r = parseInt(t.substring(2, 4), 16) / 255, s = parseInt(t.substring(4, 6), 16) / 255;
    return 0.2126 * (i <= 0.03928 ? i / 12.92 : ((i + 0.055) / 1.055) ** 2.4) + 0.7152 * (r <= 0.03928 ? r / 12.92 : ((r + 0.055) / 1.055) ** 2.4) + 0.0722 * (s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4) > 0.179 ? "#000" : "#fff";
  }
  async _submit() {
    this._submitting = !0, this._error = null;
    try {
      const e = { ...this._formData };
      this.childEntity && (e.entity_id = this.childEntity.entity_id);
      const t = this._formData._selected_timer;
      t != null && (e.timer = t), delete e._selected_timer;
      const i = this._getServiceFields(), r = this._activeExclusionGroups(i);
      for (const [s, o] of Object.entries(i))
        s !== "timer" && this._isFieldHidden(s, o, r) && delete e[s];
      await this.hass.callService("babybuddy", this.action, e), this._close();
    } catch (e) {
      this._error = e instanceof Error ? e.message : "An error occurred";
    } finally {
      this._submitting = !1;
    }
  }
  render() {
    var o, n, a;
    const e = this._getServiceFields(), t = "timer" in e, i = (a = (n = (o = this.hass) == null ? void 0 : o.services) == null ? void 0 : n.babybuddy) == null ? void 0 : a[this.action], r = (i == null ? void 0 : i.name) ?? L(this.action), s = this._activeExclusionGroups(e);
    return c`
      <div class="overlay" @click=${this._close}>
        <div
          class="dialog"
          role="dialog"
          aria-modal="true"
          aria-label=${r}
          @click=${(l) => l.stopPropagation()}
        >
          <div class="dialog-header">
            <span class="dialog-title">${r}</span>
            <button class="close-btn" @click=${this._close}>
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </div>

          <div class="dialog-body">
            ${t && this.timers.length > 0 ? c`
                  <div class="field">
                    <span>Use timer</span>
                    <div class="pill-group">
                      <button
                        type="button"
                        class="pill ${this._formData._selected_timer == null ? "active" : ""}"
                        @click=${() => this._updateField("_selected_timer", void 0)}
                      >
                        Manual
                      </button>
                      ${this.timers.map((l) => {
      const d = l.attributes.timer_id, p = l.attributes.timer_name || `Timer ${d}`, u = this._formData._selected_timer === d;
      return c`<button
                          type="button"
                          class="pill ${u ? "active" : ""}"
                          @click=${() => this._updateField("_selected_timer", d)}
                        >
                          ${p}
                        </button>`;
    })}
                    </div>
                  </div>
                ` : h}
            ${Object.entries(e).map(
      ([l, d]) => this._renderField(
        l,
        d,
        s
      )
    )}
          </div>

          ${this._error ? c`<div class="error">${this._error}</div>` : h}

          <div class="dialog-footer">
            <button class="btn cancel" @click=${this._close}>Cancel</button>
            <button
              class="btn submit"
              @click=${this._submit}
              ?disabled=${this._submitting}
            >
              ${this._submitting ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    `;
  }
  _renderField(e, t, i) {
    if (this._isFieldHidden(e, t, i)) return h;
    const r = t.name ?? L(e), s = t.selector;
    if ((s == null ? void 0 : s.boolean) != null) {
      const o = this._formData[e] === !0;
      return c`
        <div class="field">
          <span>${r}</span>
          <div class="pill-group">
            <button
              type="button"
              class="pill ${o ? "active" : ""}"
              @click=${() => this._updateField(e, !o)}
            >
              ${r}
            </button>
          </div>
        </div>
      `;
    }
    if (s != null && s.select) {
      const o = s.select.options ?? [], n = this._formData[e] ?? "";
      return c`
        <div class="field">
          <span>${r}</span>
          <div class="pill-group">
            ${o.map((a) => {
        const l = typeof a == "string" ? a : a.value, d = typeof a == "string" ? a : a.label, p = typeof a == "object" ? a.color : void 0, u = n === l, b = p ? u ? `background:${p};color:${this._textColorFor(p)};border-color:${p}` : `background:${p}22;border-color:${p}44` : "";
        return c`<button
                type="button"
                class="pill ${u ? "active" : ""} ${p ? "color-pill" : ""}"
                style=${b}
                @click=${() => this._updateField(e, u ? "" : l)}
              >
                ${d}
              </button>`;
      })}
          </div>
        </div>
      `;
    }
    if ((s == null ? void 0 : s.date) != null)
      return c`
        <label class="field">
          <span>${r}</span>
          <input
            type="date"
            .value=${this._formData[e] ?? ""}
            @input=${(o) => this._updateField(e, o.target.value)}
          />
        </label>
      `;
    if ((s == null ? void 0 : s.time) != null)
      return c`
        <label class="field">
          <span>${r}</span>
          <input
            type="time"
            .value=${this._formData[e] ?? ""}
            @input=${(o) => this._updateField(e, o.target.value)}
          />
        </label>
      `;
    if ((s == null ? void 0 : s.number) != null) {
      const o = s.number;
      return c`
        <label class="field">
          <span>${r}</span>
          <input
            type="number"
            .value=${String(this._formData[e] ?? "")}
            min=${o.min ?? h}
            max=${o.max ?? h}
            step=${o.step ?? "any"}
            @input=${(n) => {
        const a = n.target.value;
        this._updateField(e, a === "" ? void 0 : Number(a));
      }}
          />
        </label>
      `;
    }
    return (s == null ? void 0 : s.text) != null && s.text.multiline ? c`
          <label class="field">
            <span>${r}</span>
            <textarea
              rows="3"
              .value=${this._formData[e] ?? ""}
              @input=${(n) => this._updateField(
      e,
      n.target.value
    )}
            ></textarea>
          </label>
        ` : c`
      <label class="field">
        <span>${r}</span>
        <input
          type="text"
          .value=${this._formData[e] ?? ""}
          @input=${(o) => this._updateField(
      e,
      o.target.value
    )}
        />
      </label>
    `;
  }
  static get styles() {
    return F`
      .overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: flex-end;
        justify-content: center;
        z-index: 999;
        padding: 0;
        animation: fadeIn 0.2s ease;
      }
      @media (min-width: 500px) {
        .overlay {
          align-items: center;
          padding: 16px;
        }
      }
      .dialog {
        background: var(--card-background-color, var(--ha-card-background));
        border-radius: 16px 16px 0 0;
        width: 100%;
        max-width: 400px;
        max-height: 85vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: var(--ha-card-box-shadow, 0 -2px 16px rgba(0, 0, 0, 0.2));
        animation: slideUp 0.25s ease;
      }
      @media (min-width: 500px) {
        .dialog {
          border-radius: 16px;
          box-shadow: var(
            --ha-card-box-shadow,
            0 4px 24px rgba(0, 0, 0, 0.3)
          );
          animation: popIn 0.2s ease;
        }
      }
      .dialog-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px;
        border-bottom: 1px solid var(--divider-color);
      }
      .dialog-title {
        font-size: 1.1rem;
        font-weight: 500;
      }
      .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--secondary-text-color);
        padding: 4px;
        --mdc-icon-size: 20px;
      }
      .dialog-body {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        overflow-y: auto;
        flex: 1;
        min-height: 0;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 0.9rem;
        color: var(--primary-text-color);
      }
      .pill-group {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid var(--divider-color);
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
        font-size: 0.85rem;
        font-family: inherit;
        cursor: pointer;
        transition: background 0.15s, border-color 0.15s;
      }
      .pill.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }
      .pill.color-pill {
        transition: background 0.15s, border-color 0.15s, color 0.15s;
      }
      .field input[type="text"],
      .field input[type="date"],
      .field input[type="time"],
      .field input[type="number"],
      .field textarea {
        padding: 8px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
        font-size: 0.9rem;
        font-family: inherit;
      }
      .field textarea {
        resize: vertical;
        min-height: 60px;
      }
      .error {
        padding: 8px 16px;
        color: var(--error-color);
        font-size: 0.85rem;
      }
      .dialog-footer {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding: 12px 16px;
        border-top: 1px solid var(--divider-color);
      }
      .btn {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-family: inherit;
        cursor: pointer;
        border: none;
      }
      .cancel {
        background: none;
        color: var(--secondary-text-color);
      }
      .submit {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }
      .submit:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
      }
      @keyframes popIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
      }
    `;
  }
};
A([
  f({ attribute: !1 })
], w.prototype, "hass", 2);
A([
  f()
], w.prototype, "action", 2);
A([
  f({ attribute: !1 })
], w.prototype, "childEntity", 2);
A([
  f({ attribute: !1 })
], w.prototype, "timers", 2);
A([
  f({ attribute: !1 })
], w.prototype, "selects", 2);
A([
  f({ type: Number })
], w.prototype, "initialTimerId", 2);
A([
  m()
], w.prototype, "_formData", 2);
A([
  m()
], w.prototype, "_submitting", 2);
A([
  m()
], w.prototype, "_error", 2);
w = A([
  G("bb-action-dialog")
], w);
var ye = Object.defineProperty, ve = Object.getOwnPropertyDescriptor, S = (e, t, i, r) => {
  for (var s = r > 1 ? void 0 : r ? ve(t, i) : t, o = e.length - 1, n; o >= 0; o--)
    (n = e[o]) && (s = (r ? n(t, i, s) : n(s)) || s);
  return r && s && ye(t, i, s), s;
};
let v = class extends E {
  constructor() {
    super(...arguments), this._entityRegistry = [], this._registryLoaded = !1, this._activeDialog = null, this._activeTab = 0, this._sensorGroups = [], this._cardConfigLoaded = !1, this._cardConfigLoading = !1, this._cardConfigAttempts = 0, this._registryLoading = !1;
  }
  setConfig(e) {
    this._config = {
      show_timer: !0,
      show_actions: !0,
      compact: !1,
      ...e
    };
  }
  getCardSize() {
    var e;
    return (e = this._config) != null && e.compact ? 3 : 5;
  }
  getGridOptions() {
    var e;
    return {
      rows: (e = this._config) != null && e.compact ? 3 : 5,
      columns: 12,
      min_rows: 3,
      min_columns: 6
    };
  }
  static getConfigForm() {
    const e = {
      entity: "Child entity (leave empty for all children)",
      show_timer: "Show timer",
      show_actions: "Show action buttons",
      compact: "Compact mode"
    };
    return {
      schema: [
        {
          name: "entity",
          selector: { entity: { integration: "babybuddy" } }
        },
        {
          type: "expandable",
          name: "",
          title: "Display Options",
          flatten: !0,
          schema: [
            { name: "show_timer", selector: { boolean: {} } },
            { name: "show_actions", selector: { boolean: {} } },
            { name: "compact", selector: { boolean: {} } }
          ]
        }
      ],
      computeLabel: (t) => e[t.name] ?? t.name
    };
  }
  static getStubConfig() {
    return {};
  }
  connectedCallback() {
    super.connectedCallback(), this._loadEntityRegistry(), this._loadCardConfig(), this._subscribeRegistryUpdates();
  }
  disconnectedCallback() {
    var e;
    super.disconnectedCallback(), (e = this._unsubRegistry) == null || e.call(this), this._unsubRegistry = void 0;
  }
  async _subscribeRegistryUpdates() {
    if (!this._unsubRegistry)
      try {
        this._unsubRegistry = await this.hass.connection.subscribeEvents(
          (e) => {
            var i;
            const t = (i = e.data) == null ? void 0 : i.action;
            (t === "create" || t === "remove") && this._loadEntityRegistry();
          },
          "entity_registry_updated"
        );
      } catch {
      }
  }
  async _loadEntityRegistry() {
    if (!this._registryLoading) {
      this._registryLoading = !0;
      try {
        const e = await this.hass.callWS({
          type: "config/entity_registry/list"
        }), t = e.filter((i) => i.platform === "babybuddy").map((i) => i.entity_id);
        if (t.length > 0)
          try {
            const i = await this.hass.callWS({
              type: "config/entity_registry/get_entries",
              entity_ids: t
            });
            for (const r of e) {
              const s = i[r.entity_id];
              s != null && s.original_icon && (r.original_icon = s.original_icon);
            }
          } catch {
          }
        this._entityRegistry = e, this._registryLoaded = !0;
      } catch {
      } finally {
        this._registryLoading = !1;
      }
    }
  }
  async _loadCardConfig() {
    if (!(this._cardConfigLoaded || this._cardConfigLoading)) {
      this._cardConfigLoading = !0;
      try {
        const e = await this.hass.callWS({
          type: "babybuddy/card_config"
        });
        this._sensorGroups = e.sensor_groups ?? [], (e.ready ?? this._sensorGroups.length > 0) && (this._cardConfigLoaded = !0);
        const i = Qt();
        e.version !== i && this.dispatchEvent(
          new CustomEvent("hass-notification", {
            detail: {
              message: `Baby Buddy card version mismatch: backend ${e.version}, card ${i}. Please reload.`,
              duration: -1,
              dismissable: !0,
              action: {
                text: "Reload",
                action: () => {
                  const r = () => globalThis.location.reload();
                  typeof caches < "u" ? caches.keys().then(
                    (s) => Promise.all(s.map((o) => caches.delete(o)))
                  ).then(r, r) : r();
                }
              }
            },
            bubbles: !0,
            composed: !0
          })
        );
      } catch {
      } finally {
        this._cardConfigLoading = !1, this._cardConfigAttempts++, this._cardConfigAttempts >= v._MAX_CONFIG_ATTEMPTS && (this._cardConfigLoaded = !0);
      }
    }
  }
  _findChildEntityIds() {
    var e;
    return (e = this._config) != null && e.entity ? [this._config.entity] : this._registryLoaded ? this._entityRegistry.filter(
      (t) => {
        var i;
        return t.platform === "babybuddy" && t.entity_id.startsWith("sensor.") && t.original_name === null && ((i = this.hass.states[t.entity_id]) == null ? void 0 : i.state) !== "unavailable";
      }
    ).map((t) => t.entity_id) : [];
  }
  _getChildEntities(e) {
    return !this.hass || !this._registryLoaded ? null : se(e, this.hass, this._entityRegistry);
  }
  _handleAction(e) {
    this._activeDialog = e.detail.action, this._dialogTimerId = void 0;
  }
  _handleTimerStop(e) {
    this._activeDialog = e.detail.action, this._dialogTimerId = e.detail.timerId;
  }
  _handleDialogClose() {
    this._activeDialog = null, this._dialogTimerId = void 0;
  }
  updated(e) {
    super.updated(e), e.has("hass") && this.hass && (this._registryLoaded || this._loadEntityRegistry(), this._cardConfigLoaded || this._loadCardConfig());
  }
  render() {
    if (!this._config || !this.hass) return h;
    if (!this._registryLoaded)
      return c`
        <ha-card>
          <div class="loading">Loading...</div>
        </ha-card>
      `;
    const e = this._findChildEntityIds();
    if (e.length === 0)
      return c`
        <ha-card>
          <div class="not-found">
            No Baby Buddy children found. Make sure the integration is
            configured.
          </div>
        </ha-card>
      `;
    const t = Math.min(this._activeTab, e.length - 1), i = e.length > 1, r = this._config.compact ?? !1;
    return c`
      <ha-card class=${r ? "compact" : ""}>
        ${i ? this._renderTabs(e, t) : h}
        ${this._renderChild(e[t])}
      </ha-card>
    `;
  }
  _renderTabs(e, t) {
    return c`
      <div class="tabs" role="tablist">
        ${e.map((i, r) => {
      const s = this.hass.states[i], o = (s == null ? void 0 : s.attributes.friendly_name) ?? i, n = r === t;
      return c`
            <button
              class="tab ${n ? "active" : ""}"
              role="tab"
              aria-selected=${n}
              @click=${() => {
        this._activeTab = r, this._activeDialog = null, this._dialogTimerId = void 0;
      }}
            >
              ${o}
            </button>
          `;
    })}
      </div>
    `;
  }
  _renderChild(e) {
    const t = this._getChildEntities(e);
    if (!(t != null && t.primary))
      return c`
        <div class="not-found">
          Entity ${e} not found or not loaded yet.
        </div>
      `;
    const i = t.primary, r = i.attributes.birth_date ?? i.state, s = i.attributes.friendly_name ?? i.entity_id, o = i.attributes.entity_picture;
    return c`
      <bb-child-header
        .name=${s}
        .age=${ie(r)}
        .picture=${o}
        .compact=${this._config.compact ?? !1}
      ></bb-child-header>

      ${this._config.show_timer ? c`
            <bb-timer-bar
              .hass=${this.hass}
              .timers=${t.timers}
              .startTimerButton=${t.startTimerButton}
              .childEntityId=${e}
              @bb-timer-stop=${this._handleTimerStop}
            ></bb-timer-bar>
          ` : h}

      ${this._config.show_actions ? c`
            <bb-action-buttons
              .hass=${this.hass}
              .childEntity=${i}
              .entityRegistry=${this._entityRegistry}
              .compact=${this._config.compact ?? !1}
              @bb-action=${this._handleAction}
            ></bb-action-buttons>
          ` : h}

      <bb-activity-chips
        .hass=${this.hass}
        .sensors=${t.sensors}
        .binarySensors=${t.binarySensors}
        .entityRegistry=${this._entityRegistry}
        .childPrefix=${i.entity_id.split(".")[1] ?? ""}
        .sensorGroups=${this._sensorGroups}
        .compact=${this._config.compact ?? !1}
      ></bb-activity-chips>
      ${this._activeDialog ? c`
            <bb-action-dialog
              .hass=${this.hass}
              .action=${this._activeDialog}
              .childEntity=${i}
              .timers=${t.timers}
              .selects=${t.selects}
              .initialTimerId=${this._dialogTimerId}
              @bb-dialog-close=${this._handleDialogClose}
            ></bb-action-dialog>
          ` : h}
    `;
  }
  static get styles() {
    return F`
      :host {
        display: block;
      }
      ha-card {
        padding: 16px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      ha-card.compact {
        padding: 10px;
        gap: 8px;
      }
      .not-found {
        padding: 16px;
        text-align: center;
        color: var(--secondary-text-color);
        font-size: 0.9rem;
      }
      .loading {
        padding: 24px 16px;
        text-align: center;
        color: var(--secondary-text-color);
        font-size: 0.9rem;
      }
      .loading::after {
        content: "";
        display: block;
        width: 24px;
        height: 24px;
        margin: 12px auto 0;
        border: 2px solid var(--divider-color);
        border-top-color: var(--primary-color);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
      .tabs {
        display: flex;
        gap: 4px;
        margin-bottom: 12px;
        border-bottom: 1px solid var(--divider-color);
        padding-bottom: 8px;
        overflow-x: auto;
        scrollbar-width: none;
      }
      .tabs::-webkit-scrollbar {
        display: none;
      }
      .tab {
        padding: 6px 14px;
        border: none;
        border-radius: 16px;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
        font-size: 0.85rem;
        font-family: inherit;
        font-weight: 500;
        white-space: nowrap;
        transition: all 0.2s ease;
        outline: none;
      }
      .tab.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }
      @media (hover: hover) {
        .tab:not(.active):hover {
          background: var(--secondary-background-color);
        }
      }
      .tab:not(.active):focus-visible {
        background: var(--secondary-background-color);
      }
      .tab:focus-visible {
        box-shadow: 0 0 0 2px var(--primary-color);
      }
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
    `;
  }
};
v._MAX_CONFIG_ATTEMPTS = 10;
S([
  f({ attribute: !1 })
], v.prototype, "hass", 2);
S([
  m()
], v.prototype, "_config", 2);
S([
  m()
], v.prototype, "_entityRegistry", 2);
S([
  m()
], v.prototype, "_registryLoaded", 2);
S([
  m()
], v.prototype, "_activeDialog", 2);
S([
  m()
], v.prototype, "_dialogTimerId", 2);
S([
  m()
], v.prototype, "_activeTab", 2);
S([
  m()
], v.prototype, "_sensorGroups", 2);
v = S([
  G("babybuddy-card")
], v);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "babybuddy-card",
  name: "Baby Buddy",
  preview: !0,
  description: "Track feedings, sleep, diapers, and more",
  documentationURL: "https://github.com/eyalmichon/ha-babybuddy"
});
export {
  v as BabyBuddyCard
};
