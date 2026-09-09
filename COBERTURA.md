# Cobertura do renderizador — lista das ~100 figuras

As ~100 figuras da lista NÃO viram ~100 funções. Elas colapsam em **~13 geradores
paramétricos** — é isso que faz a ferramenta ser "universal":

| gerador | cobre | como |
|---|---|---|
| `figura(spec)` | trapézios, triângulos, qualquer polígono nomeado, marcações | composição de primitivas (pontos/segmentos/ângulos/marcas/cotas) |
| `formas.triangulo(tipo)` | os 6 triângulos | 6 conjuntos de 3 pontos + marcas |
| `formas.quadrilatero(tipo)` | os 8 quadriláteros | idem, 4 pontos |
| `formas.poligono_regular(n)` | pentágono … **megágono (n=10⁶)** | 1 fórmula: n vértices no círculo (acima de ~60 lados é um círculo, e essa é a lição) |
| `formas.estrela(n, k)` | pentagrama … decagrama | símbolo de Schläfli {n/k}; gcd(n,k)≠1 vira composto (hexagrama = 2 triângulos) |
| `formas.curva(nome)` | elipse, parábola, hipérbole, cardioide, lemniscata, espiral, óvalo de Cassini | equação paramétrica |
| `formas.parte_circulo(nome)` | círculo, circunferência, semicírculo, setor, segmento, coroa | recorte de arco/anel |
| `solidos.solido(nome)` | 5 platônicos + 6 arquimedianos | vértices → arestas por distância → projeção trimétrica |
| `solidos._truncar(V, t)` | os 6 sólidos de Arquimedes da lista | corta os vértices de um platônico (t=⅓ trunca, t=½ retifica) |
| corpos redondos | esfera, cilindro, cone, tronco, toro, elipsoide, paraboloide, hiperboloide | elipse achatada = "circunferência vista de lado" |
| `solidos._prisma/_piramide/...` | prismas, pirâmides, troncos, antiprisma, bipirâmide (qualquer nº de lados) | polígono base extrudado / com ápice |

Ressalvas visuais conhecidas (renderiza, mas dá pra caprichar): **toro** (leitura de
volume fraca), **cuboctaedro / octaedro truncado** (aresta oculta pela heurística de
profundidade, não por faces). **Kepler-Poinsot** exige lógica de auto-interseção —
único item ainda não coberto.


**97/98 figuras renderizam.**  ✅ sai da ferramenta hoje · ⚠️ renderiza com ressalva · ❌ ainda não coberto

## I. Figuras planas (2D)


### triângulos

- ✅ equilatero
- ✅ isosceles
- ✅ escaleno
- ✅ retangulo
- ✅ acutangulo
- ✅ obtusangulo

### quadriláteros

- ✅ quadrado
- ✅ retangulo
- ✅ losango
- ✅ paralelogramo
- ✅ trapezio_isosceles
- ✅ trapezio_retangulo
- ✅ trapezio_escaleno
- ✅ deltoide

### polígonos regulares

- ✅ pentágono (n=5)
- ✅ hexágono (n=6)
- ✅ heptágono (n=7)
- ✅ octógono (n=8)
- ✅ eneágono (n=9)
- ✅ decágono (n=10)
- ✅ hendecágono (n=11)
- ✅ dodecágono (n=12)
- ✅ 13-ágono (n=13)
- ✅ 14-ágono (n=14)
- ✅ pentadecágono (n=15)
- ✅ 16-ágono (n=16)
- ✅ 17-ágono (n=17)
- ✅ 18-ágono (n=18)
- ✅ 19-ágono (n=19)
- ✅ icoságono (n=20)
- ✅ 21-ágono (n=21)
- ✅ 22-ágono (n=22)
- ✅ 23-ágono (n=23)
- ✅ 24-ágono (n=24)
- ✅ 25-ágono (n=25)
- ✅ 26-ágono (n=26)
- ✅ 27-ágono (n=27)
- ✅ 28-ágono (n=28)
- ✅ 29-ágono (n=29)
- ✅ triacontágono (n=30)

### polígonos de muitos lados

- ✅ tetracontágono (n=40)
- ✅ pentacontágono (n=50)
- ✅ hectágono (n=100)
- ✅ chiliágono (n=1.000)
- ✅ miriágono (n=10.000)
- ✅ megágono (n=1.000.000)

### círculo e partes

- ✅ circulo
- ✅ circunferencia
- ✅ semicirculo
- ✅ setor
- ✅ segmento
- ✅ coroa

### curvas

- ✅ elipse
- ✅ parabola
- ✅ hiperbole
- ✅ cardioide
- ✅ lemniscata
- ✅ espiral
- ✅ cassini

### estrelas

- ✅ pentagrama
- ✅ hexagrama
- ✅ heptagrama
- ✅ octagrama
- ✅ eneagrama
- ✅ decagrama

## II. Figuras espaciais (3D)


### sólidos platônicos

- ✅ tetraedro
- ✅ cubo
- ✅ octaedro
- ✅ dodecaedro
- ✅ icosaedro

### corpos redondos

- ✅ esfera
- ✅ hemisferio
- ✅ cilindro
- ✅ cone
- ✅ tronco_cone
- ✅ toro
- ✅ elipsoide
- ✅ paraboloide
- ✅ hiperboloide

### prismas

- ✅ prisma triangular
- ✅ paralelepípedo
- ✅ prisma pentagonal
- ✅ prisma hexagonal
- ✅ prisma octogonal

### pirâmides

- ✅ pirâmide quadrangular
- ✅ pirâmide pentagonal
- ✅ tronco de pirâmide

### sólidos de Arquimedes

- ✅ tetraedro_truncado
- ✅ cuboctaedro
- ✅ cubo_truncado
- ✅ octaedro_truncado
- ✅ icosidodecaedro
- ✅ icosaedro_truncado

### outros

- ✅ prisma oblíquo
- ✅ antiprisma triangular
- ✅ cilindro oblíquo
- ✅ bipirâmide quadrada
- ❌ Kepler-Poinsot (poliedro estrelado)
