import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ShoppingCart, ChevronLeft, ChevronRight, Sparkles, ExternalLink } from 'lucide-react';
import { Banner } from '../types';

interface HeroBannerSliderProps {
  banners?: Banner[];
  compact?: boolean;
  onCtaClick?: () => void;
}

interface SlideItem {
  id: number;
  title: string;
  subtitle: string;
  image_url: string;
  button_text?: string;
  link_url?: string;
  is_base?: boolean;
}

const BASE_HERO_SLIDE: SlideItem = {
  id: 0,
  title: 'هيبة الأصل... جمال الكهرمان',
  subtitle: 'مسابيح وأحجار طبيعية ونوادر مختارة بعناية لعشاق التميز',
  image_url: '/branding/hero-amber.jpg',
  button_text: 'تسوق المجموعة',
  link_url: '#products-section',
  is_base: true
};

export const HeroBannerSlider: React.FC<HeroBannerSliderProps> = ({
  banners = [],
  compact = false,
  onCtaClick
}) => {
  // 1. Build slides list: Always starts with the permanent base slide, followed by active custom announcement banners
  const activeBanners = banners.filter((b) => b.is_active === 1 || b.is_active === true);
  const slides: SlideItem[] = [
    BASE_HERO_SLIDE,
    ...activeBanners.map((b) => ({
      id: b.id,
      title: b.title || 'هيبة الأصل... جمال الكهرمان',
      subtitle: b.subtitle || 'مسابيح وأحجار طبيعية ونوادر مختارة بعناية لعشاق التميز',
      image_url: b.image_url,
      button_text: b.button_text || 'تسوق المجموعة',
      link_url: b.link_url || '#products-section',
      is_base: false
    }))
  ];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const touchStartX = useRef<number | null>(null);

  const totalSlides = slides.length;

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % totalSlides);
  }, [totalSlides]);

  const goToPrev = useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + totalSlides) % totalSlides);
  }, [totalSlides]);

  const goToSlide = (idx: number) => {
    setCurrentIndex(idx);
  };

  // 2. Auto-advance interval (5.5 seconds, pauses when hovered or touched)
  useEffect(() => {
    if (totalSlides <= 1 || isPaused) return;

    const timer = setInterval(() => {
      goToNext();
    }, 5500);

    return () => clearInterval(timer);
  }, [totalSlides, isPaused, goToNext]);

  // Handle CTA button click
  const handleAction = (slide: SlideItem) => {
    if (onCtaClick) {
      onCtaClick();
      return;
    }
    const link = slide.link_url || '#products-section';
    if (link.startsWith('#')) {
      const targetId = link.replace('#', '');
      const el = document.getElementById(targetId);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    } else if (link.startsWith('http://') || link.startsWith('https://') || link.startsWith('//')) {
      window.open(link, '_blank', 'noopener,noreferrer');
    } else {
      window.location.href = link;
    }
  };

  // Touch Swipe Handlers for Mobile
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    setIsPaused(true);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) {
      setIsPaused(false);
      return;
    }
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartX.current - touchEndX;

    // RTL gesture: swiping left goes to next, swiping right goes to prev
    if (Math.abs(diff) > 40) {
      if (diff > 0) {
        goToNext();
      } else {
        goToPrev();
      }
    }
    touchStartX.current = null;
    setIsPaused(false);
  };

  // --- A. MOBILE COMPACT HERO CARD ---
  if (compact) {
    const currentSlide = slides[currentIndex] || BASE_HERO_SLIDE;
    return (
      <div
        className="relative rounded-2xl overflow-hidden min-h-[160px] flex items-center p-4 shadow-sm border border-[#EBE3D5] select-none group"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {/* Slides Images Stack with Smooth Crossfade */}
        {slides.map((s, idx) => (
          <img
            key={`${s.id}-${idx}`}
            src={s.image_url || '/branding/hero-amber.jpg'}
            alt={s.title}
            className={`absolute inset-0 w-full h-full object-cover object-center transition-opacity duration-700 ease-in-out ${
              idx === currentIndex ? 'opacity-100 scale-100' : 'opacity-0 scale-105 pointer-events-none'
            }`}
          />
        ))}

        {/* Gradient Overlay for Mobile Readability */}
        <div className="absolute inset-0 bg-gradient-to-l from-black/85 via-black/55 to-black/25 pointer-events-none" />

        {/* Mobile Content */}
        <div className="relative z-10 space-y-1.5 text-right max-w-[80%]">
          <span className="inline-flex items-center gap-1 text-[9px] font-black bg-[#C9972B] text-black px-2 py-0.5 rounded-full shadow-xs">
            <Sparkles className="w-2.5 h-2.5 text-black" />
            <span>{currentSlide.is_base ? 'نوادر هيبة السلطان 2026' : 'إعلان خاص حصري'}</span>
          </span>

          <h2 className="text-base sm:text-lg font-black text-white leading-tight drop-shadow-sm line-clamp-2">
            {currentSlide.title}
          </h2>

          <p className="text-[10px] text-white/90 leading-relaxed font-medium line-clamp-2">
            {currentSlide.subtitle}
          </p>

          <div className="pt-1">
            <button
              type="button"
              onClick={() => handleAction(currentSlide)}
              className="inline-flex items-center gap-1 px-3 py-1 bg-white/90 hover:bg-white text-[#26221C] text-[10px] font-bold rounded-lg shadow-xs active:scale-95 transition"
            >
              <span>{currentSlide.button_text || 'تسوق الآن'}</span>
              <ChevronLeft className="w-3 h-3 text-[#9A6817]" />
            </button>
          </div>
        </div>

        {/* Mobile Slider Indicator Dots */}
        {totalSlides > 1 && (
          <div className="absolute bottom-2.5 left-3 flex items-center gap-1.5 z-20">
            {slides.map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => goToSlide(idx)}
                aria-label={`الشريحة ${idx + 1}`}
                className={`transition-all duration-300 rounded-full cursor-pointer ${
                  idx === currentIndex
                    ? 'w-5 h-1.5 bg-[#C9972B] shadow-xs'
                    : 'w-1.5 h-1.5 bg-white/60 hover:bg-white'
                }`}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // --- B. DESKTOP PANORAMIC HERO SECTION ---
  const currentSlide = slides[currentIndex] || BASE_HERO_SLIDE;

  return (
    <div
      className="relative w-full min-h-[380px] sm:min-h-[460px] md:min-h-[520px] flex items-center justify-center overflow-hidden select-none group"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Slides Background Images with Smooth Crossfade */}
      {slides.map((s, idx) => (
        <div
          key={`${s.id}-${idx}`}
          className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
            idx === currentIndex ? 'opacity-100 z-0' : 'opacity-0 z-0 pointer-events-none'
          }`}
        >
          <img
            src={s.image_url || '/branding/hero-amber.jpg'}
            alt={s.title}
            fetchPriority={idx === 0 ? 'high' : 'auto'}
            decoding="async"
            className="w-full h-full object-cover object-center transform transition-transform duration-7000 ease-out scale-100 hover:scale-103"
          />
        </div>
      ))}

      {/* Subtle Gradient Overlays for Enhanced Typography Contrast */}
      <div className="absolute inset-0 bg-gradient-to-r from-black/40 via-black/15 to-black/40 pointer-events-none z-1" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/20 pointer-events-none z-1" />

      {/* Central Hero Content Box */}
      <div className="relative z-10 text-center px-4 max-w-3xl mx-auto space-y-4">
        {!currentSlide.is_base && (
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[#C9972B]/90 backdrop-blur-xs text-[#12100D] font-black text-xs shadow-md mb-1 animate-fade-in">
            <Sparkles className="w-3.5 h-3.5" />
            <span>عرض وإعلان مميز</span>
          </div>
        )}

        <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white drop-shadow-[0_2px_12px_rgba(0,0,0,0.85)] tracking-tight leading-tight">
          {currentSlide.title}
        </h1>

        <p className="text-sm sm:text-base md:text-lg font-medium text-white max-w-xl mx-auto leading-relaxed drop-shadow-[0_2px_10px_rgba(0,0,0,0.85)]">
          {currentSlide.subtitle}
        </p>

        <div className="pt-2">
          <button
            type="button"
            onClick={() => handleAction(currentSlide)}
            className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-full bg-[#C9972B] hover:bg-[#B8851E] text-white font-black text-sm sm:text-base shadow-[0_6px_25px_rgba(201,151,43,0.4)] hover:shadow-2xl transition-all transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
          >
            <ShoppingCart className="w-4 h-4" />
            <span>{currentSlide.button_text || 'تسوق المجموعة'}</span>
          </button>
        </div>
      </div>

      {/* Previous / Next Arrow Controls (Desktop only, visible if > 1 slide) */}
      {totalSlides > 1 && (
        <>
          <button
            type="button"
            onClick={goToPrev}
            aria-label="الشريحة السابقة"
            className="absolute right-4 sm:right-6 top-1/2 -translate-y-1/2 z-20 w-11 h-11 rounded-full bg-black/35 hover:bg-[#C9972B] text-white border border-white/20 hover:border-[#C9972B] backdrop-blur-md flex items-center justify-center transition-all duration-200 shadow-lg opacity-80 hover:opacity-100 hover:scale-105 active:scale-95 cursor-pointer"
          >
            <ChevronRight className="w-6 h-6" />
          </button>

          <button
            type="button"
            onClick={goToNext}
            aria-label="الشريحة التالية"
            className="absolute left-4 sm:left-6 top-1/2 -translate-y-1/2 z-20 w-11 h-11 rounded-full bg-black/35 hover:bg-[#C9972B] text-white border border-white/20 hover:border-[#C9972B] backdrop-blur-md flex items-center justify-center transition-all duration-200 shadow-lg opacity-80 hover:opacity-100 hover:scale-105 active:scale-95 cursor-pointer"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
        </>
      )}

      {/* Carousel Pagination Dots */}
      {totalSlides > 1 && (
        <div className="absolute bottom-5 inset-x-0 flex items-center justify-center gap-2 z-20">
          {slides.map((s, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => goToSlide(idx)}
              aria-label={`الانتقال إلى الشريحة ${idx + 1}`}
              className={`transition-all duration-300 rounded-full cursor-pointer ${
                idx === currentIndex
                  ? 'w-8 h-2.5 bg-[#C9972B] shadow-md ring-2 ring-white/60'
                  : 'w-2.5 h-2.5 bg-white/70 hover:bg-white hover:scale-110'
              }`}
              title={s.is_base ? 'الرئيسية (الثابتة)' : s.title}
            />
          ))}
        </div>
      )}
    </div>
  );
};
