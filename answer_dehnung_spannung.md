Hier ist eine ausführliche, lehrbuchartige Erklärung der mechanischen Grundlagen von Spannungen und Dehnungen, basierend auf den bereitgestellten Unterlagen.

---

# 1. Dehnungen (Strain)

Die **Dehnung** (im Deutschen auch *Dehnung ε* genannt) ist eine kinematische Größe. Sie beschreibt die Geometrie der Verformung eines elastischen Körpers und ist ein Maß für die relative Längenänderung eines Stabes oder Materials. Da es sich um das Verhältnis zweier Längen handelt, ist die Dehnung **dimensionslos**.

### Definition und Formel
Für einen Stab der ursprünglichen Länge $l$, der sich um $\Delta l$ verändert, definiert sich die technische Dehnung $\varepsilon$ allgemein als:
$$ \varepsilon = \frac{\Delta l}{l} $$
Auf einer lokalen, punktuellen Ebene wird die Dehnung durch die Verschiebung $u(x)$ entlang der Stabachse beschrieben. Die örtliche Dehnung ist die Ableitung der Verschiebung nach dem Ort $x$:
$$ \varepsilon(x) = \frac{du}{dx} = u'(x) $$

*   **Formelzeichen:** $\varepsilon$ (Epsilon)
*   **Einheit:** dimensionslos [-] (oder z.B. mm/mm)

### Vorzeichen und Annahmen (Gültigkeitsgrenzen)
*   **Positiv (+):** Verlängerung des Stabes (Zugdehnung, $\Delta l > 0$).
*   **Negativ (-):** Verkürzung des Stabes (Druckdehnung, $\Delta l < 0$).
*   **Gültigkeitsgrenze:** Die klassische Definition der technischen Dehnung setzt **kleine Deformationen** voraus ($|\Delta l| \ll l$ bzw. $|\varepsilon| \ll 1$).

### Konkretes Beispiel: Dehnung eines Stabelements
Betrachtet man einen Stab mit einer ortsabhängigen Querschnittsfläche, bei dem die Verschiebung $u(x)$ entlang der Achse variiert, so lässt sich die Längenänderung durch Integration der Dehnung ermitteln:
$$ u(x) = \int \varepsilon(x) dx $$

---

# 2. Spannungen und Normalspannungen

Während die Dehnung die *Verformung* (Kinematik) beschreibt, ist die **Spannung** ($\sigma$) eine Kraftgröße (Dynamik). Sie ist ein Maß für die innere Beanspruchung des Materials und repräsentiert die Flächenkräfte in der Schnittebene eines Körpers pro Flächeneinheit. 

Nach der Definition von Augustin Louis Cauchy wird die technische Spannung berechnet, indem die innere Normalkraft $N$ durch die Fläche $A$ geteilt wird.

### Definition der Normalspannung
Die **Normalspannung** ist der Anteil der Spannung, der *senkrecht* (normal) zu einer Schnittfläche wirkt. Für einen prismatischen Stab unter axialer Belastung gilt:
$$ \sigma = \frac{N}{A} = \frac{F}{A} $$
*(Hinweis: Bei der wahren Spannung $\sigma_w$ wird die tatsächliche, sich veränderliche Querschnittsfläche $A_w$ während der Belastung verwendet: $\sigma_w = \frac{F}{A_w}$.)*

*   **Formelzeichen:** $\sigma$ (Sigma)
*   **Einheit:** $[MPa] = [N/mm^2]$

### Vorzeichenkonvention und Zug/Druck
*   **Zugstab:** Die Normalkraft $N$ ist positiv gerichtet ($N > 0$). Daraus folgt eine positive Spannung ($\sigma > 0$), was als **Zugspannung** bezeichnet wird. Die Kräfte wirken nach außen.
*   **Druckstab:** Die Normalkraft ist negativ ($N < 0$). Daraus folgt eine negative Spannung ($\sigma < 0$), die **Druckspannung**. (Achtung: Bei schlanken Stäben kann unter Druck vor Erreichen der Fließgrenze ein Knicken eintreten).

### Abgrenzung zur Schubspannung und der Spannungstensor
Der vollständige Spannungszustand in einem Punkt wird durch den **Spannungstensor** (Tensor 2. Stufe) beschrieben, der in eine $3 \times 3$-Matrix eingebettet ist. 
*   **Normalspannungen** ($\sigma_x, \sigma_y, \sigma_z$) befinden sich auf der Hauptdiagonale des Tensors. Sie wirken senkrecht zur Schnittebene.
*   **Schubspannungen** ($\tau_{xy}, \tau_{yx}$, etc.) sind die übrigen Komponenten des Tensors. Sie wirken *in* der Schnittebene (tangential).
Aufgrund von Momentengleichgewichten ist der Spannungstensor symmetrisch ($\tau_{xy} = \tau_{yx}$), weshalb er aus nur sechs unabhängigen Einträgen besteht.

### Hauptspannungen (Principal Stresses)
Abhängig vom Schnittwinkel $\varphi$ verändern sich Normal- und Schubspannungen. Die **Hauptspannungen** ($\sigma_1, \sigma_2$) sind die Extremalwerte (Maximum und Minimum) der Normalspannung. 
In den Schnittrichtungen (Hauptachsen), in denen die Hauptspannungen auftreten, **verschwinden die Schubspannungen** ($\tau_{\xi\eta} = 0$). Sie berechnen sich für den ebenen Spannungszustand (ESZ) analytisch durch Nullsetzen der Ableitung der Schubspannung nach dem Winkel (Extremwertbestimmung) zu:
$$ \sigma_{1,2} = \frac{\sigma_x + \sigma_y}{2} \pm \sqrt{\left(\frac{\sigma_x - \sigma_y}{2}\right)^2 + \tau_{xy}^2} $$

### Konkretes Beispiel: Konischer Druckstab
Ein konischer Stab (Länge $l$, Endradien $r_0$ und $2r_0$) wird durch eine axiale Druckkraft $F$ belastet. 
*   **Geometrie:** Der Radius ändert sich über die Länge: $r(x)$. Die Fläche ist $A(x) = \pi \cdot r(x)^2$.
*   **Normalkraft:** Da der Stab nur am Ende belastet wird, ist die innere Normalkraft konstant: $N(x) = -F$.
*   **Normalspannung:** Die Spannung wird ortsabhängig:
$$ \sigma(x) = \frac{N(x)}{A(x)} = \frac{-F}{\pi \cdot r(x)^2} \quad \text{(Druckspannung, da negativ)} $$

---

# 3. Zusammenhang: Stoffgesetz und Hooke'sches Gesetz

Das **Stoffgesetz** (oder Materialmodell) schlägt die theoretische Brücke zwischen Kinematik (Dehnung $\varepsilon$) und Kinetik (Spannung $\sigma$). Da dieses Modell materialabhängig ist, muss es experimentell (z. B. im Zug- oder Druckversuch) ermittelt und im **Spannungs-Dehnungs-Diagramm** dargestellt werden.

### Elastisches und Plastisches Materialverhalten
Im Spannungs-Dehnungs-Diagramm lassen sich verschiedene Phasen unterscheiden:
1.  **Elastischer Bereich** ($|\sigma| < \sigma_F$, wobei $\sigma_F$ die Fließgrenze/Yield Strength ist): Das Material nimmt nach vollständiger Entlastung seine ursprüngliche Länge wieder an.
2.  **Linear-elastischer Bereich** ($\sigma \leq \sigma_p$, wobei $\sigma_p$ die Proportionalitätsgrenze ist): In diesem Bereich herrscht eine strikt lineare Proportionalität zwischen Spannung und Dehnung.
3.  **Plastischer Bereich** ($|\sigma| > \sigma_F$): Bei völliger Entlastung bleibt eine permanente Verformung im Körper zurück, die sogenannte plastische Dehnung $\varepsilon_{pl}$.

### Das Hooke'sche Gesetz
Für den linearelastischen Bereich gilt das **Hooksche Modell** (Hooke's Law). Es besagt, dass die Spannung direkt proportional zur Dehnung ist. Der Proportionalitätsfaktor ist der **Elastizitätsmodul** $E$ (Young's Modulus), ein spezifischer Materialkennwert.
$$ \sigma = E \cdot \varepsilon $$
Umgestellt nach der Dehnung ergibt sich:
$$ \varepsilon = \frac{\sigma}{E} = \frac{N}{E \cdot A} $$
Das Produkt aus Elastizitätsmodul $E$ und Querschnittsfläche $A$ wird als **Dehnsteifigkeit** ($EA$) bezeichnet und bestimmt den Widerstand des Stabes gegen Verformung.
Aus integriertem Hooke's Gesetz folgt für die Stabverlängerung:
$$ \Delta l = \frac{F \cdot l}{E \cdot A} $$

*   **Formelzeichen:** $E$ (Elastizitätsmodul)
*   **Einheit:** $[MPa] = [N/mm^2]$

### Temperaturdehnung (Thermoelastizität)
Dehnung muss nicht ausschließlich durch Kräfte verursacht werden. Ändert sich die Temperatur eines Stabes um $\Delta T$, erfährt er eine thermische Ausdehnung (Wärmedehnung), die über den thermischen Ausdehnungskoeffizienten $\alpha_T$ beschrieben wird.
Das erweiterte, thermoelastische Stoffgesetz (Duhamel-Neumann) setzt sich aus mechanischer und thermischer Dehnung zusammen:
$$ \varepsilon = \frac{\sigma}{E} + \alpha_T \cdot \Delta T $$
Die Gesamtängenänderung eines Stabes unter Kraft- und Temperatureinfluss errechnet sich somit zu:
$$ \Delta l = \int_0^l \left( \frac{N}{E \cdot A} + \alpha_T \cdot \Delta T \right) dx $$

*(Anmerkung zur Querkontraktion/Poissonzahl: In den bereitgestellten Lehrdokumenten wird die Poissonzahl $\nu$ lediglich als zweiter Parameter im isotropen Stoffgesetz $\sigma_{ij} = 2\mu\varepsilon_{ij} + \lambda\varepsilon_{kk}\delta_{ij}$ (Lamé-Parameter) am Rande erwähnt. Eine detaillierte, herleitende Formel oder Definition zur Querkontraktion in Stäben ist im vorliegenden Kontext nicht enthalten.)*

---

# 4. Herleitung des Stabproblems (Einzelstab)

Um Spannungen und Verformungen eines Stabes zu berechnen, müssen drei fundamental verschiedene Gleichungstypen kombiniert werden:
1.  **Gleichgewichtsbedingung:** Verknüpft äußere Kräfte mit der inneren Normalkraft $N(x)$.
2.  **Kinematik:** Verknüpft Verschiebung $u(x)$ mit der Dehnung $\varepsilon(x) = u'(x)$.
3.  **Elastizitätsgesetz:** Verknüpft Kraft und Verformung ($\sigma = E \cdot \varepsilon$).

Fasst man diese drei Gleichungen zusammen, erhält man die **Differentialgleichung für die Verschiebung** eines Stabes:
$$ E \cdot A \cdot \frac{du}{dx} = N(x) + E \cdot A \cdot \alpha_T \cdot \Delta T $$

### Konkretes Beispiel: Statisch unbestimmtes System (Beidseitig eingespannter Stab unter Thermik)
Ein Stab ist an *beiden* Enden fest eingespannt (Lager A und B) und wird gleichförmig um $\Delta T$ erwärmt. Gesucht sind die Lagerreaktionen.
*   **Analyse:** Da das System statisch unbestimmt ist, reichen die Gleichgewichtsbedingungen nicht aus, um die Normalkraft zu bestimmen. 
*   **Gleichgewicht:** $B - C = 0$ (Die Lagerkräfte heben sich auf).
*   **Randbedingung (Kinematik):** Da der Stab beidseitig fest ist, darf er sich in der Summe nicht verlängern: $\Delta l = 0$.
*   **Lösung:** Im Gegensatz zu einem statisch bestimmten System, das sich frei ausdehnen würde ($\Delta l > 0$), baut das feste Einspannsystem hier eine mechanische Druckspannung auf, die die Wärmedehnung exakt kompensiert. Nach dem Prinzip der Superposition führt die Randbedingung $u_c = u_c^{(0)} + u_c^{(1)} = 0$ zur Bestimmung der unbekannten Stabkräfte.

### References

- [1] Kapitel10_Elastostatik_Zug_und_Druck_in_Stäben.pdf
- [2] Kapitel11_Spannungszustand.pdf
