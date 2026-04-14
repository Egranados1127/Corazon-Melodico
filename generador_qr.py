import qrcode
import os
import argparse

def generate_qrs(base_url, bar_id, max_mesas=41):
    output_dir = f"qrs_impresion_{bar_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Empezamos a redactar el archivo HTML para la hoja de impresión
    html_content = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <title>Lámina QR - {bar_id}</title>
    <style>
        body {{ 
            font-family: 'Helvetica Neue', Arial, sans-serif; 
            text-align: center; 
            background: #f4f4f4;
            padding: 20px;
        }}
        .print-btn {{
            padding: 12px 25px; 
            font-size: 18px; 
            font-weight: bold;
            background-color: #D4AF37;
            color: #000;
            border: none;
            border-radius: 8px;
            margin-bottom: 30px; 
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .print-btn:hover {{ background-color: #b5952f; }}
        
        .qr-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .qr-card {{ 
            background: #fff;
            border: 2px dashed #D4AF37; 
            padding: 15px; 
            border-radius: 12px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            page-break-inside: avoid;
        }}
        img {{ max-width: 100%; height: auto; }}
        .header-text {{ font-size: 12px; font-weight: bold; color: #888; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }}
        .mesa-number {{ font-size: 28px; font-weight: 900; margin-top: 5px; color: #4A0E0E; }}
        .scan-text {{ font-size: 13px; color: #333; font-weight: bold; margin-top: 5px; }}
        
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .print-btn {{ display: none; }}
            .qr-card {{ border: 1px solid #ccc; }}
        }}
    </style>
    </head>
    <body>
    <h1 style="color: #4A0E0E;">Lámina de Códigos QR para el Bar: {bar_id}</h1>
    <button class="print-btn" onclick="window.print()">🖨️ Mandar a Imprimir</button>
    <div class="qr-grid">
    """
    
    # Bucle para generar las 41 mesas
    for mesa in range(1, max_mesas + 1):
        url = f"{base_url}/?bar={bar_id}&mesa={mesa}"
        
        # Crear la imagen del código QR
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#111111", back_color="white")
        
        img_filename = f"Mesa_{mesa}.png"
        filepath = os.path.join(output_dir, img_filename)
        img.save(filepath)
        
        # Añadir al documento HTML
        html_content += f"""
        <div class="qr-card">
            <div class="header-text">Punto Desiderata</div>
            <img src="{img_filename}" alt="Mesa {mesa}">
            <div class="mesa-number">MESA {mesa}</div>
            <div class="scan-text">Escanea para pedir música</div>
        </div>
        """
        
    html_content += "</div></body></html>"
    
    # Guardar la hoja web
    html_path = os.path.join(output_dir, "hoja_de_impresion.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("\n" + "="*50)
    print(f"🎉 ¡ÉXITO! Se generaron {max_mesas} códigos QR para '{bar_id}'.")
    print(f"📁 Todas las imágenes se guardaron en la carpeta: {output_dir}")
    print(f"💡 Para INPRIMIRLOS fácilmente:")
    print(f"   1. Entra a la carpeta '{output_dir}'.")
    print(f"   2. Haz doble clic en el archivo 'hoja_de_impresion.html'.")
    print(f"   3. Cuando abra en Chrome/Edge, dale al botón amarillo de Imprimir.")
    print("="*50 + "\n")

if __name__ == "__main__":
    print("==================================")
    print(" MÁQUINA DE CÓDIGOS QR MASIVOS")
    print("==================================")
    print("Vamos a generar tus 40 códigos QR listos para imprimir.")
    
    bar_num = input("Ingresa el ID corporativo del bar (Ej. '1' o 'bar_1'): ").strip()
    if not bar_num:
        print("Tratando de generar para testing...")
        bar_num = "bar_1"
    
    # Auto-corrección si el usuario olvidó el prefijo oficial de Supabase
    if not bar_num.startswith("bar_"):
        bar_num = f"bar_{bar_num}"
        
    dominio = input("Ingresa la URL pública de la web (o presiona ENTER para usar localhost por ahora): ").strip()
    if not dominio:
        dominio = "http://localhost:8501"
        
    maximas = input("¿Cuántas mesas quieres generar? (Por defecto 41): ").strip()
    if not maximas:
        maximas = 41
    else:
        maximas = int(maximas)
        
    generate_qrs(dominio, bar_num, max_mesas=maximas)
