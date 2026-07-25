# Dehnungen, Spannungen und Normalspannungen

**Frage:** Was sind Dehnungen und Spannungen, wie hängen diese zusammen und was sind Normalspannungen?

**Quellen (LightRAG, hybrid/mix):**
- Kapitel10_Elastostatik_Zug_und_Druck_in_Stäben.pdf
- Kapitel11_Spannungszustand.pdf

**Erstellt:** 2026-07-24

---

## 1. Verzerrungszustand und Dehnungen

Die Dehnung (Verzerrung) beschreibt die kinematische Veränderung der Geometrie eines elastischen Körpers unter Belastung. Sie ist eine **kinematische Größe** — im Gegensatz zur Spannung, die eine Kraftgröße ist.

### Technische Dehnung

Dimensionslos, Kleinheitsannahme ε ≪ 1:

$$\varepsilon = \frac{\Delta l}{l}$$

- Δl > 0 → Verlängerung → positive Dehnung (Zug)
- Δl < 0 → Verkürzung → negative Dehnung (Druck/Stauchung)

### Lokale Dehnung

Bei ortsabhängiger Querschnittsfläche oder Verschiebung u(x) ist die Dehnung die erste räumliche Ableitung der Verschiebungsfunktion:

$$\varepsilon(x) = \frac{du}{dx} \qquad\Longrightarrow\qquad u(x) = \int \varepsilon(x)\,dx$$

**Anwendung:** konischer Stab mit veränderlichem Radius r(x) und Querschnittsfläche A(x) = π·r(x)², was zu einer ortsabhängigen Dehnung führt.

---

## 2. Spannungen

Spannungen sind innere Kraftgrößen und Maß für die Beanspruchung des Materials. Symbol **σ**, übliche Einheit MPa = N/mm².

Grundlegende Definition über Normal-/Axialkraft und Querschnittsfläche:

$$\sigma = \frac{N}{A} = \frac{F}{A}$$

### Schnittprinzip und Spannungsvektor

Ein gedachter Schnitt (z. B. s–s) durch den Körper macht die inneren Kräfte sichtbar. Äußere Belastungen (Einzelkräfte F_i, Flächenlasten p) verursachen über die Schnittfläche A verteilte innere Kräfte — die Spannungen.

Der Spannungsvektor **t** beschreibt die Spannung in einem beliebigen Punkt einer Schnittfläche. Er hängt ab von:
- dem **Ort** im Körper
- der **Orientierung** der Schnittfläche (Normalenvektor **n**)

Ein einzelner Spannungsvektor reicht nicht aus, um den vollständigen Spannungszustand in einem Punkt zu beschreiben.

### Normalspannung σ vs. Schubspannung τ

Der Spannungsvektor zerlegt sich in zwei Komponenten:

| Komponente | Wirkrichtung | Notation |
|---|---|---|
| **Normalspannung σ** | senkrecht (normal) zur Schnittfläche | σ_x, σ_y, σ_z |
| **Schubspannung τ** | tangential in der Schnittfläche | Doppelindex, z. B. τ_xy |

Vorzeichen der Normalspannung: positiv = Zugspannung, negativ = Druckspannung.

### Cauchy-Spannungstensor und Symmetrie

Zur eindeutigen Festlegung des Spannungszustands in einem Punkt betrachtet man drei senkrecht aufeinanderstehende Schnittflächen (analog zu den Koordinatenebenen). Die Komponenten der zugehörigen Spannungsvektoren bilden eine 3×3-Matrix, den **Spannungstensor**:

$$\boldsymbol{\sigma} =
\begin{pmatrix}
\sigma_{xx} & \tau_{xy} & \tau_{xz} \\
\tau_{yx} & \sigma_{yy} & \tau_{yz} \\
\tau_{zx} & \tau_{zy} & \sigma_{zz}
\end{pmatrix}$$

- **Hauptdiagonale:** Normalspannungen (σ_xx, σ_yy, σ_zz, kurz σ_x, σ_y, σ_z)
- **Übrige Komponenten:** Schubspannungen

Aus dem **Momentengleichgewicht** um die Achsen durch den Mittelpunkt eines infinitesimalen Volumenelements folgt zwingend die Symmetrie des Spannungstensors:

$$\tau_{xy} = \tau_{yx}, \qquad \tau_{xz} = \tau_{zx}, \qquad \tau_{yz} = \tau_{zy}$$

Damit reduziert sich die Zahl der unabhängigen Komponenten von neun auf **sechs**.

---

## 3. Zusammenhang: Materialgesetz

Das Stoffgesetz (Materialmodell) beschreibt die physikalische Beziehung zwischen kinematischen Größen (Dehnungen) und Kraftgrößen (Spannungen). Es ist materialabhängig und wird experimentell durch Zug- oder Druckversuche ermittelt.

### Spannungs-Dehnungs-Diagramm

Im Zugversuch wird ein Probenstab gedehnt; Kraft und Längenänderung werden als σ über ε aufgetragen.

- **Linear-elastischer Bereich** (|σ| < σ_F): Material verhält sich elastisch. Nach vollständiger Entlastung nimmt der Stab seine ursprüngliche Länge wieder an.
- **Plastischer Bereich** (|σ| > σ_F): Überschreiten der Fließgrenze σ_F führt zu plastischer Verformung. Nach Entlastung bleibt eine permanente plastische Dehnung ε_pl zurück.

### Hookesches Gesetz (einachsig)

Im Rahmen der linearen Elastizitätstheorie, solange σ ≤ σ_p (Proportionalitätsgrenze), ist die Normalspannung direkt proportional zur Dehnung:

$$\sigma = E \cdot \varepsilon \qquad\Longleftrightarrow\qquad \varepsilon = \frac{\sigma}{E}$$

Der Proportionalitätsfaktor **E** ist der Elastizitätsmodul (Young's Modulus), ein Maß für die Steifigkeit des Materials.

### Verallgemeinertes Hookesches Gesetz

Für mehrachsige Spannungszustände tensoriell erweitert:

$$\boldsymbol{\sigma} = \boldsymbol{E} \cdot \boldsymbol{\varepsilon}$$

**E** ist dabei ein Tensor vierter Stufe, der den Verzerrungstensor auf den Spannungstensor abbildet.

### Temperaturdehnung

Bei Temperaturänderung ΔT entsteht eine thermische Dehnung. Die Gesamtlängenänderung setzt sich aus mechanischem und thermischem Anteil zusammen:

$$\Delta l = \int_0^l \left( \frac{N}{EA} + \alpha_T \, \Delta T \right) dx$$

mit N = Normalkraft, α_T = thermischer Ausdehnungskoeffizient.

- **Statisch bestimmte Systeme:** Temperaturänderung verursacht nur Verformungen.
- **Statisch unbestimmte Systeme:** zusätzlich entstehen **Wärmespannungen**.

---

## 4. Normalspannungen im Detail: Transformation und Hauptspannungen

Ändert sich die Schnittrichtung durch einen belasteten Punkt (Drehung um Winkel φ), so ändern sich die Werte für Normal- und Schubspannung.

### Spannungstransformation (ebener Spannungszustand)

Für eine dünne Scheibe (ESZ), Drehung des Koordinatensystems um φ:

$$\sigma_{\xi} = \tfrac{1}{2}(\sigma_x + \sigma_y) + \tfrac{1}{2}(\sigma_x - \sigma_y)\cos 2\varphi + \tau_{xy}\sin 2\varphi$$

$$\sigma_{\eta} = \tfrac{1}{2}(\sigma_x + \sigma_y) - \tfrac{1}{2}(\sigma_x - \sigma_y)\cos 2\varphi - \tau_{xy}\sin 2\varphi$$

$$\tau_{\xi\eta} = -\tfrac{1}{2}(\sigma_x - \sigma_y)\sin 2\varphi + \tau_{xy}\cos 2\varphi$$

**Invariante** des Spannungstensors (unveränderlich bei Rotation) — die Summe der Normalspannungen:

$$\sigma_x + \sigma_y = \sigma_{\xi} + \sigma_{\eta}$$

### Hauptspannungen und Hauptrichtungen

Unter den Hauptrichtungen φ* erreichen die Normalspannungen ihre Extremalwerte — die Hauptspannungen σ_1, σ_2. In genau diesen Schnitten **verschwindet die Schubspannung** (τ_ξη = 0):

$$\sigma_{1,2} = \frac{\sigma_x + \sigma_y}{2} \pm \sqrt{\left(\frac{\sigma_x - \sigma_y}{2}\right)^2 + \tau_{xy}^2}$$

Winkel der Hauptrichtungen:

$$\tan 2\varphi^* = \frac{2\tau_{xy}}{\sigma_x - \sigma_y}$$

Die **maximalen Schubspannungen** (Hauptschubspannungen) treten in Schnitten auf, die um 45° zu den Hauptrichtungen geneigt sind:

$$\varphi^{**} = \varphi^* \pm \frac{\pi}{4}$$

### Mohrscher Spannungskreis

Graphische Methode zur Darstellung und Bestimmung der Spannungstransformation. Die Punkte (σ, τ) aller möglichen Schnittrichtungen liegen auf einem Kreis in der σ-τ-Ebene.

- Normalspannungen bilden die **horizontale Achse**, Schubspannungen die vertikale.
- Mittelpunkt: M(σ_M, 0) mit $\sigma_M = \dfrac{\sigma_x + \sigma_y}{2}$
- Die Schnittpunkte des Kreises mit der σ-Achse entsprechen den Hauptspannungen σ_1 und σ_2.

### Sonderfall: hydrostatischer Spannungszustand

Die Normalspannungen sind in allen Schnittrichtungen gleich groß und unabhängig vom Winkel φ; die Schubspannungen verschwinden vollständig. Der Mohrsche Kreis entartet zu einem Punkt.

---

## 5. Typische Anwendungsbeispiele

1. **Dimensionierung eines Zugstabes** — die erforderliche Querschnittsfläche A_erf wird so gewählt, dass eine vorgegebene maximale Normalspannung nicht überschritten wird. Für einen konischen Druckstab gilt lokal σ(x) = N(x)/A(x).

2. **Statisch bestimmte Stabsysteme** — Verschiebung eines Knotenpunktes: zuerst Stabkräfte über Gleichgewichtsbedingungen, daraus Spannung, Dehnung und Längenänderung

   $$\Delta l = \frac{F \cdot l}{EA}$$

3. **Statisch unbestimmte Systeme** — beidseitig eingespannter, erwärmter Stab. Das Kräftegleichgewicht reicht nicht aus; zusätzlich müssen Kinematik und Elastizitätsgesetz herangezogen werden, um Lagerreaktionen und Wärmespannungen zu bestimmen. Randbedingung: Δl = 0.

---

## Anhang: Lücken im Wissensgraph

Folgende Unterthemen sind in den aktuell ingestierten Quellen **nicht** enthalten:

- Querdehnung und Querkontraktionszahl (Poissonzahl ν)
- Gleitung/Schiebung γ, Verzerrungstensor, Volumendehnung
- Schubmodul G und der Zusammenhang $G = \dfrac{E}{2(1+\nu)}$
- Streckgrenze, Zugfestigkeit, Bruch im Zugversuch (nur Fließgrenze σ_F behandelt)
- Vergleichsspannungen (von Mises, Tresca)
- Ausgeführte Beispiele für einachsigen Zug und reinen Schub

Die Datei `IN/Kapitel12_Verzerrungszustand.pdf` liegt noch nicht im Wissensgraph. Ein Ingest dieses Kapitels dürfte den Verzerrungstensor, ν und γ ergänzen.
