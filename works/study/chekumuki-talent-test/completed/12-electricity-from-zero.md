# Electricity from Zero: Volts, Amps, Watts and More ⚡

**You don't need to understand electricity already.** Start with sections 1–5. They explain the words first; the maths comes later in small steps. This is an independent learning guide, not an official Chekumuki syllabus. Your teacher's textbook and competition instructions take priority.

**Safety first:** Never experiment with a wall socket, exposed wires, damaged chargers or household mains. Even a small battery can become dangerously hot if short-circuited. If you want a real demonstration, ask a teacher to supervise a suitable low-voltage kit; do not connect a battery directly across itself.

**Other guides:** [Chekumuki pack](README.md) · [Easy maths and reasoning](03-easy-maths-and-reasoning.md) · [Fast knowledge cards](11-fast-deep-knowledge-cards.md).

---

## 1. The big picture: what happens when a bulb lights?

Imagine a simple circuit made of a battery, connecting wires, a switch and a suitable bulb. When the switch is closed and everything is connected correctly, there is a complete path. The battery's chemical processes help maintain a **potential difference** across its terminals. An electric current flows, and the bulb transfers electrical energy into light and heat.

```text
        switch          bulb
   + ─── o──o ───────── ( X ) ───┐
 battery                          │
   − ─────────────────────────────┘
```

This is a simplified picture, not a construction guide. **Current is flow of electric charge; energy is what the bulb transfers.** The battery supplies energy; the charge moving through the wire is not the same thing as the energy it transfers.

## 2. Charge: the starting ingredient

- **Electric charge (విద్యుత్ ఆవేశం)** is a property of matter. There are positive and negative charges.
- **Electrons** have negative charge; **protons** have positive charge. In a metal wire, mobile electrons carry charge through the metal. In a liquid containing ions, moving ions can carry charge too.
- The unit of charge is the **coulomb (C)**. One coulomb is a quantity of charge, like a litre is a quantity of water—but charge and water are different things.
- A coulomb is a large amount of charge on the scale of individual electrons: roughly **6.24 × 10¹⁸ electrons** have a total charge of −1 C. You do not need to memorise that huge number to understand circuits.

## 3. ★ Current: how quickly charge flows

**Electric current (విద్యుత్ ప్రవాహం)** tells us the rate of flow of electric charge.

> **Current = charge transferred ÷ time**
> **I = Q ÷ t**

- **I** = current, measured in **amperes (A)**, also called **amps**.
- **Q** = charge, measured in **coulombs (C)**.
- **t** = time, measured in **seconds (s)**.
- **1 ampere = 1 coulomb per second.**

**Example:** If 6 C of charge pass a point in 3 seconds, current = 6 ÷ 3 = **2 A**.

A larger current means more charge passes a point per second. **It does not by itself say how much energy each coulomb carries:** for that, we need voltage.

### Which way does it flow?

By convention, current direction is the direction positive charge would move: in the external part of a simple battery circuit, from the battery's positive terminal towards its negative terminal. In a metal wire the mobile electrons drift in the opposite direction. Both descriptions can be used consistently; quiz questions usually use **conventional current** unless they ask about electrons.

## 4. ★ Potential difference and voltage: energy per charge

**Potential difference (విద్యుత్ పొటెన్షియల్ భేదం)** between two points tells us how much energy is transferred **per unit charge** between those points. Its unit is the **volt (V)**. In everyday speech, potential difference is often called **voltage**.

> **Voltage = energy transferred ÷ charge**
> **V = E ÷ Q**

- **1 volt = 1 joule per coulomb.**
- A potential difference of **6 V** across a component corresponds to **6 joules of energy transferred per coulomb of charge** passing through it, in this simple circuit model.
- Voltage is always a **difference between two points**. A battery can have a voltage across its terminals even when the switch is open and no current flows in the external circuit.

**Example:** If 2 C passes through a component with 6 V across it, energy transferred = 6 J/C × 2 C = **12 J**.

**A gentle distinction:** Electric *potential* is energy per unit charge at a point relative to a chosen reference. *Potential difference* compares the potentials at two points. A voltmeter measures the difference—not an absolute voltage floating on its own.

## 5. ★ Resistance: how a component opposes current

**Resistance (నిరోధం)** describes how strongly a component opposes electric current for an applied voltage. Its unit is the **ohm (Ω)**.

For an **ohmic** component under suitable constant conditions, Ohm's law says:

> **Voltage = current × resistance**
> **V = I × R**

So **I = V ÷ R** and **R = V ÷ I**.

**Example:** A 6 Ω resistor with 12 V across it carries current I = 12 ÷ 6 = **2 A**, if it behaves ohmically under those conditions.

If the voltage stays the same, increasing resistance decreases current in this simple model. If resistance stays the same, increasing voltage increases current.

**Important:** Not every component has constant resistance. A filament bulb heats up as current changes, so the simple constant-resistance calculation may not accurately describe it over its full range. Real batteries and wires also have resistance.

## 6. One analogy: a pump and a loop of water

Imagine a **closed loop** of pipe filled with water, with a pump and a narrow section:

| Electricity | Water-loop analogy | The simple idea |
|---|---|---|
| Charge | Water | The quantity that moves around the loop |
| Current (A) | Flow rate | How much passes a point per second |
| Voltage (V) | Pressure difference | The energy supplied or transferred per unit of the moving quantity |
| Resistance (Ω) | Narrowness or restriction | How much the path opposes flow |
| Battery | Pump | Supplies energy to help maintain the difference |

**Where the analogy breaks:** Electricity is not literal water in wires. Charges already exist throughout a metal wire; they are not used up by the bulb. A battery transforms chemical energy, and the bulb transfers electrical energy. The water analogy helps build intuition, but it does not explain every circuit or how electrical energy moves through fields.

## 7. ★ Power and watts: how fast energy is transferred

**Electrical power (విద్యుత్ శక్తి వినియోగ రేటు)** is the rate at which energy is transferred or used.

> **Power = energy ÷ time**
> **P = E ÷ t**
> **1 watt (W) = 1 joule per second (J/s)**

For a simple DC component, or when voltage and current values are appropriate for the circuit:

> **Power = voltage × current**
> **P = V × I**

**Example:** A device with 6 V across it and a current of 2 A transfers electrical energy at **6 × 2 = 12 W**, or **12 joules each second**.

If it runs at that power for 5 seconds, it transfers **12 × 5 = 60 J**. Real devices' power can change as they operate.

### A note on AC

For alternating current, using RMS voltage × RMS current gives **apparent power** in volt-amperes (VA). Real average power in watts also depends on power factor. At beginner level, use P = VI for the simple DC examples here; don't assume it gives real power for every AC device.

## 8. ★ Energy and your electricity bill: watts are not watt-hours

- A **watt (W)** is a rate: how fast energy is transferred.
- A **watt-hour (Wh)** is an amount of energy: power in watts × time in hours.
- **1 kilowatt (kW) = 1,000 W.**
- **1 kilowatt-hour (kWh) = 1,000 Wh = 3.6 million joules.**
- One electricity-bill **unit** usually means **1 kWh of electrical energy**, not 1 kW of power.

**Example A:** A 100 W lamp runs for 5 hours at constant power.

1. Energy = 100 W × 5 h = **500 Wh**.
2. 500 Wh ÷ 1,000 = **0.5 kWh**, or half a unit.

**Example B:** A 2,000 W heater runs for 30 minutes at constant power.

1. 2,000 W = 2 kW; 30 minutes = 0.5 hour.
2. Energy = 2 kW × 0.5 h = **1 kWh**, or one unit.

A bill also depends on tariff slabs, taxes and other charges. Actual consumption may differ from a label if a device cycles on and off or does not run at its rated power throughout.

## 9. Four words that are easy to mix up

| Quantity | Plain meaning | Unit | What a bigger number means |
|---|---|---|---|
| **Charge Q** | Quantity of electric charge | coulomb (C) | More charge |
| **Current I** | Charge passing a point per second | ampere (A) | Faster charge flow |
| **Voltage V** | Energy transferred per unit charge between two points | volt (V) | More joules per coulomb |
| **Resistance R** | Opposition to current for an applied voltage | ohm (Ω) | At the same voltage, less current in the simple ohmic model |
| **Power P** | Energy transferred per second | watt (W) | Faster energy transfer |
| **Energy E** | Amount of energy transferred | joule (J) or kWh | More total energy |

**Memory sentence:** “**Volts** give energy per charge, **amps** count charge per second, **ohms** oppose current, and **watts** count energy per second.”

## 10. Open and closed circuits

- **Closed circuit:** a complete conducting path exists. If a suitable source provides a potential difference, current can flow.
- **Open circuit:** the path is broken, for example by an open switch; no sustained current flows around the broken simple circuit. The battery can still have voltage across its terminals.
- **Short circuit:** an unintended low-resistance path can cause dangerously large current and heating. Do not make one; ask an adult to handle damaged equipment.
- **Conductors**, such as many metals, allow charge to move readily. **Insulators**, such as intact dry plastic, resist charge flow much more strongly. Real materials are not perfect conductors or insulators under all conditions.

## 11. Series and parallel, without fear

### Series: one path

```text
 battery ── resistor A ── resistor B ── back to battery
```

- The **same current** flows through components in a simple single-loop series circuit.
- If one component opens, the path is broken for the whole loop.
- Series resistances add: **2 Ω + 4 Ω = 6 Ω**. With an ideal 12 V source, total current = 12/6 = **2 A**.
- Voltage divides across the resistors: 2 A × 2 Ω = 4 V and 2 A × 4 Ω = 8 V; together they add to 12 V.

### Parallel: multiple branches

```text
                 ┌── resistor A ──┐
 battery ────────┤                ├──── back to battery
                 └── resistor B ──┘
```

- Each branch is connected across the same two points, so each has the **same voltage** across it.
- Current splits between branches. The source current is the **sum** of the branch currents.
- Example: two 6 Ω resistors in parallel across an ideal 12 V source each carry 12/6 = **2 A**. Total current = 2 + 2 = **4 A**. Equivalent resistance = 12 V / 4 A = **3 Ω**.
- For these resistors, opening one branch leaves the other path intact. Actual household circuits include protective devices and must be handled only by qualified people.

## 12. Measuring instruments

- An **ammeter** measures current and is connected **in series** with the component being measured, using the correct range.
- A **voltmeter** measures potential difference and is connected **in parallel** across the two points being compared.
- A **multimeter** may perform several functions, but an incorrect setting or connection can damage equipment or cause injury. Do not use one on mains; learn with a teacher and suitable equipment.

**Memory trick:** **A**mmeter joins the route; **V**oltmeter views across two points.

## 13. DC, AC and common devices

- **DC (direct current):** current flows in one direction in the simple model. A battery supplies DC; its output need not be perfectly constant in every situation.
- **AC (alternating current):** current reverses direction periodically. Household supply is AC, but **mains electricity is dangerous**—do not touch or test it.
- **Cell and battery:** a cell converts chemical energy into electrical energy. A battery can contain multiple cells; in everyday speech the words are sometimes used loosely.
- **Motor:** mainly converts electrical energy into mechanical motion, with some energy also transferred as heat and sound.
- **Generator:** converts mechanical energy into electrical energy through electromagnetic induction. It does not create energy from nothing.
- **Fuse:** a safety component designed to melt and break the circuit if current is excessive. It is not a substitute for safe wiring; never replace a fuse with ordinary wire.

## 14. Common questions and traps

**Is voltage the same as current?** No. Voltage is energy per unit charge; current is charge per second. You can have voltage across an open battery circuit with zero external current.

**Does a bulb consume current?** In a simple series loop, the same current passes into and out of the bulb. The bulb transfers energy; it does not use up the charge.

**Is a 100 W appliance always more expensive than a 60 W appliance?** Not necessarily. Total energy depends on **power and time**. A 100 W lamp for 1 h uses 0.1 kWh; a 60 W lamp for 10 h uses 0.6 kWh.

**Does a higher voltage always mean a higher current?** Not by itself. Current also depends on the circuit and component. For the *same ohmic resistance* under suitable conditions, increasing voltage increases current.

**Does a larger current always mean greater power?** Not without knowing voltage. In a simple DC device, compare P = VI. A 2 A current at 3 V gives 6 W; 1 A at 12 V gives 12 W.

**Does a battery store volts?** Better to say a battery stores chemical energy and provides a potential difference. Voltage describes energy per charge, not the total amount of energy stored.

## 15. Practice: do it yourself first

1. What does current measure?
2. What is the unit of potential difference?
3. What does 1 volt mean in joules and coulombs?
4. Can an open circuit have voltage across a battery but no external current?
5. If 12 C passes a point in 4 s, what is the current?
6. If 3 C passes through a component with 5 V across it, how much energy is transferred?
7. A 4 Ω ohmic resistor has 8 V across it. Find the current.
8. A device takes 3 A at 6 V DC. Find its power.
9. A 60 W lamp runs for 5 h. Find its energy use in kWh.
10. A 1 kW heater runs for 30 minutes at constant power. How many kWh?
11. In a single-loop series circuit, is the current the same through both resistors?
12. In a parallel circuit, do branches across the same two points have the same voltage?
13. Two 3 Ω resistors are connected in series. What is their total resistance?
14. Two 6 Ω resistors are connected in parallel across an ideal 12 V source. What is the current in each branch?
15. Is an ammeter connected in series or parallel to measure a component's current?
16. Is a voltmeter connected in series or parallel to measure a component's voltage?
17. In a metal wire, do electrons drift in the same direction as conventional current or the opposite direction?
18. A 12 W device runs at that power for 5 seconds. How much energy does it transfer?
19. Which is an amount of energy: kW or kWh?
20. Does a fuse make it safe to touch exposed mains wires?

### Answers and the reason

1. **Charge flow per second.** 2. **Volt (V).** 3. **One joule per coulomb.** 4. **Yes:** the battery can maintain a terminal voltage even though the external path is broken. 5. **3 A:** 12 C ÷ 4 s. 6. **15 J:** 5 J/C × 3 C. 7. **2 A:** I = V/R = 8/4. 8. **18 W:** P = VI = 6 × 3. 9. **0.3 kWh:** 60 × 5 = 300 Wh. 10. **0.5 kWh:** 1 kW × 0.5 h.

11. **Yes**, in a simple single loop. 12. **Yes:** they are connected across the same two points. 13. **6 Ω:** series resistances add. 14. **2 A per branch:** I = 12/6. 15. **Series.** 16. **Parallel.** 17. **Opposite:** electrons are negatively charged. 18. **60 J:** 12 J/s × 5 s. 19. **kWh:** kW is power. 20. **No:** exposed mains wiring is dangerous; keep away and tell an adult.

## 16. Quick revision plan

- **First 10 minutes:** Read sections 3–5. Explain amps, volts and ohms without a formula.
- **Next 10 minutes:** Read sections 7–9. Calculate the lamp and heater examples yourself.
- **Last 10 minutes:** Try questions 1–10, then check answers. Tomorrow, review anything confusing and try 11–20.

**If you remember only one line:** voltage tells you **energy per charge**; current tells you **charge per second**; multiplying them gives **energy per second**, or power.

## Further reading

- [NCERT Class 10 science materials](https://ncert.nic.in/textbook.php): choose your edition and the electricity chapter.
- [NCERT exemplar problems](https://ncert.nic.in/exemplar-problems.php?ln=/): school-level practice. Your local textbooks and teacher's guidance take priority.
