/**
 * Utility for high-performance client-side image compression.
 * Compresses raw high-res images (5-15MB) into lightweight WebP/JPEG (~80-150KB)
 * directly in the browser canvas before uploading to the server.
 */

export interface CompressionResult {
  dataUrl: string;
  originalSize: number;
  compressedSize: number;
  reductionPercent: number;
  width: number;
  height: number;
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export async function compressImageFile(
  file: File,
  maxDimension: number = 1400,
  quality: number = 0.82
): Promise<CompressionResult> {
  return new Promise((resolve, reject) => {
    // Basic validation
    if (!file.type.startsWith('image/')) {
      return reject(new Error('الملف المختار ليس صورة صالحة'));
    }

    const originalSize = file.size;
    const reader = new FileReader();

    reader.onerror = () => reject(new Error('فشل قراءة ملف الصورة من جهازك'));

    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error('فشل معالجة أبعاد الصورة'));

      img.onload = () => {
        try {
          let { width, height } = img;

          // Scale down proportionally if larger than maxDimension
          if (width > maxDimension || height > maxDimension) {
            if (width > height) {
              height = Math.round((height * maxDimension) / width);
              width = maxDimension;
            } else {
              width = Math.round((width * maxDimension) / height);
              height = maxDimension;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;

          const ctx = canvas.getContext('2d');
          if (!ctx) {
            return reject(new Error('تعذر إنشاء سياق المعالجة الرسومية'));
          }

          // Use high-quality interpolation
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';

          // Fill white background for transparent PNGs converting to JPEG/WebP
          ctx.fillStyle = '#FFFFFF';
          ctx.fillRect(0, 0, width, height);

          // Draw scaled image
          ctx.drawImage(img, 0, 0, width, height);

          // Export as WebP first, fallback to JPEG
          let dataUrl = canvas.toDataURL('image/webp', quality);
          if (!dataUrl.startsWith('data:image/webp')) {
            dataUrl = canvas.toDataURL('image/jpeg', quality);
          }

          // Calculate approximate byte size from Base64 string
          const base64Length = dataUrl.length - (dataUrl.indexOf(',') + 1);
          const compressedSize = Math.round((base64Length * 3) / 4);

          const reductionPercent = Math.max(
            0,
            Math.round(((originalSize - compressedSize) / originalSize) * 100)
          );

          resolve({
            dataUrl,
            originalSize,
            compressedSize,
            reductionPercent,
            width,
            height
          });
        } catch (err: any) {
          reject(new Error(err?.message || 'حدث خطأ أثناء ضغط الصورة'));
        }
      };

      img.src = reader.result as string;
    };

    reader.readAsDataURL(file);
  });
}
