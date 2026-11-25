import React, { useState, useEffect } from 'react';
import { notificationManager, ToastItem, ConfirmDialogOptions } from '../utils/toast';
import { 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  X, 
  Crown,
  HelpCircle,
  Sparkles
} from 'lucide-react';

export const RoyalNotifications: React.FC = () => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [confirmDialog, setConfirmDialog] = useState<(ConfirmDialogOptions & { resolve: (val: boolean) => void }) | null>(null);

  useEffect(() => {
    const unsubToasts = notificationManager.subscribeToasts(setToasts);
    const unsubConfirm = notificationManager.subscribeConfirm(setConfirmDialog);

    // Friendly monkeypatch for window.alert so even untranslated alerts never look like ugly browser dialogs
    const originalAlert = window.alert;
    window.alert = (message?: any) => {
      const msgStr = typeof message === 'string' ? message : String(message ?? '');
      if (msgStr.includes('🎉') || msgStr.includes('✅') || msgStr.includes('نجاح') || msgStr.includes('مرحباً')) {
        notificationManager.show('success', msgStr, 'هيبة السلطان');
      } else if (msgStr.includes('❌') || msgStr.includes('خطأ') || msgStr.includes('فشل') || msgStr.includes('تعذر') || msgStr.includes('⛔')) {
        notificationManager.show('error', msgStr, 'تنبيه');
      } else if (msgStr.includes('⚠️') || msgStr.includes('يرجى') || msgStr.includes('يجب') || msgStr.includes('انتهت')) {
        notificationManager.show('warning', msgStr, 'ملاحظة هامة');
      } else {
        notificationManager.show('info', msgStr, 'إشعار');
      }
    };

    return () => {
      unsubToasts();
      unsubConfirm();
      window.alert = originalAlert;
    };
  }, []);

  const getToastIcon = (type: ToastItem['type']) => {
    switch (type) {
      case 'success':
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-[#C9972B]/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0 shadow-lg shadow-emerald-900/20">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
        );
      case 'error':
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500/20 to-amber-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400 shrink-0 shadow-lg shadow-rose-900/20">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
          </div>
        );
      case 'warning':
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-[#C9972B]/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 shadow-lg shadow-amber-900/20">
            <AlertCircle className="w-5 h-5 text-amber-400" />
          </div>
        );
      case 'info':
      default:
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#C9972B]/30 to-[#9A6817]/20 border border-[#C9972B]/40 flex items-center justify-center text-[#E2B84B] shrink-0 shadow-lg shadow-amber-900/20">
            <Crown className="w-5 h-5 text-[#E2B84B]" />
          </div>
        );
    }
  };

  return (
    <>
      {/* Toast Notifications Container */}
      <div 
        className="fixed top-5 left-1/2 -translate-x-1/2 md:translate-x-0 md:left-6 md:right-auto z-[999999] flex flex-col gap-3 pointer-events-none w-[92vw] max-w-md"
        dir="rtl"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto relative overflow-hidden rounded-2xl bg-[#17140F]/95 backdrop-blur-xl border border-[#C9972B]/40 shadow-2xl shadow-black/80 p-4 transition-all duration-300 animate-in fade-in slide-in-from-top-4"
            style={{
              boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.7), 0 0 20px 0 rgba(201, 151, 43, 0.15)'
            }}
          >
            {/* Top golden accent line */}
            <div className="absolute top-0 right-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-[#C9972B] to-transparent" />

            <div className="flex items-start gap-3.5">
              {getToastIcon(t.type)}
              <div className="flex-1 min-w-0 pt-0.5">
                {t.title && (
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-xs font-bold text-[#E2B84B] tracking-wide flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-[#C9972B]" />
                      {t.title}
                    </span>
                  </div>
                )}
                <p className="text-sm text-[#F8F4EB] leading-relaxed font-normal select-text whitespace-pre-line">
                  {t.message}
                </p>
              </div>

              <button
                type="button"
                onClick={() => notificationManager.dismiss(t.id)}
                className="text-[#9E9484] hover:text-[#F8F4EB] p-1.5 rounded-lg hover:bg-white/5 transition-colors shrink-0"
                title="إغلاق"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Subtle countdown bar */}
            {t.duration && t.duration > 0 && (
              <div className="absolute bottom-0 right-0 left-0 h-[2px] bg-white/10 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-l from-[#C9972B] to-[#E2B84B] animate-[progress_linear_forwards]"
                  style={{ animationDuration: `${t.duration}ms` }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Royal Confirmation Modal */}
      {confirmDialog && (
        <div 
          className="fixed inset-0 z-[9999999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
          dir="rtl"
        >
          <div 
            className="relative w-full max-w-md overflow-hidden rounded-2xl bg-gradient-to-b from-[#1C1813] to-[#12100D] border border-[#C9972B]/50 p-6 shadow-2xl shadow-black transition-all animate-in zoom-in-95 duration-200"
            style={{
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.9), 0 0 35px 2px rgba(201, 151, 43, 0.2)'
            }}
          >
            {/* Ambient gold glow */}
            <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-48 h-48 bg-[#C9972B]/20 rounded-full blur-3xl pointer-events-none" />

            {/* Header Icon Emblem */}
            <div className="flex flex-col items-center text-center mb-5">
              <div className="relative mb-3.5">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#26221C] to-[#17140F] border border-[#C9972B]/50 flex items-center justify-center shadow-xl shadow-amber-950/40">
                  {confirmDialog.type === 'danger' ? (
                    <AlertTriangle className="w-8 h-8 text-rose-400" />
                  ) : confirmDialog.type === 'warning' ? (
                    <HelpCircle className="w-8 h-8 text-amber-400" />
                  ) : (
                    <Crown className="w-8 h-8 text-[#E2B84B]" />
                  )}
                </div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-[#C9972B] text-[#12100D] flex items-center justify-center shadow-md">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
              </div>

              <h3 className="text-lg font-bold text-[#E2B84B] tracking-wide mb-1.5">
                {confirmDialog.title || 'هيبة السلطان - تأكيد الإجراء'}
              </h3>
              
              <p className="text-sm text-[#F8F4EB]/90 leading-relaxed font-normal whitespace-pre-line px-2">
                {confirmDialog.message}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-[#C9972B]/20">
              <button
                type="button"
                onClick={() => confirmDialog.resolve(false)}
                className="flex-1 py-2.5 px-4 rounded-xl border border-[#C9972B]/30 hover:bg-[#C9972B]/10 text-[#E9DECB] font-medium text-sm transition-all text-center active:scale-95"
              >
                {confirmDialog.cancelText || 'إلغاء'}
              </button>

              <button
                type="button"
                onClick={() => confirmDialog.resolve(true)}
                className={`flex-1 py-2.5 px-4 rounded-xl font-bold text-sm text-white shadow-lg transition-all text-center active:scale-95 ${
                  confirmDialog.type === 'danger'
                    ? 'bg-gradient-to-r from-rose-700 to-rose-600 hover:from-rose-600 hover:to-rose-500 shadow-rose-900/30'
                    : 'bg-gradient-to-r from-[#9A6817] via-[#C9972B] to-[#E2B84B] hover:brightness-110 shadow-amber-900/30 text-[#12100D]'
                }`}
              >
                {confirmDialog.confirmText || 'تأكيد'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default RoyalNotifications;
