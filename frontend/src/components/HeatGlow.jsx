/**
 * HeatGlow.jsx — Camada de brilho de calor (leaflet.heat) sobre o choropleth.
 * Recebe pontos [lat, lng, intensidade] e desenha um halo quente nos focos.
 * Falha de forma silenciosa se o plugin leaflet.heat não estiver disponível.
 */
import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';

export default function HeatGlow({ points, options }) {
  const map = useMap();
  useEffect(() => {
    if (!map || !points || !points.length || typeof L.heatLayer !== 'function') return undefined;
    let layer;
    try {
      layer = L.heatLayer(points, {
        radius: 10,
        blur: 16,
        max: 2.8,
        minOpacity: 0.06,
        gradient: {
          0.35: 'rgba(245,158,11,0)',
          0.60: 'rgba(249,115,22,.45)',
          0.82: 'rgba(249,115,22,.85)',
          1.00: '#ef4444',
        },
        ...options,
      });
      layer.addTo(map);
    } catch (err) {
      // Falha silenciosa: o choropleth continua; só o brilho de calor não aparece.
      console.warn('HeatGlow indisponível:', err?.message || err);
      return undefined;
    }
    return () => {
      try {
        if (layer) map.removeLayer(layer);
      } catch {
        /* noop */
      }
    };
  }, [points, options, map]);
  return null;
}
