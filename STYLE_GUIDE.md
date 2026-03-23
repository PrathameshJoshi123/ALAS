# ALAS Frontend - Component & Style Guide

## 🎨 Design Tokens

### Color Palette

#### Primary Colors

- **slate-50**: #F8FAFC (lightest background)
- **slate-100**: #F1F5F9
- **slate-200**: #E2E8F0
- **slate-300**: #CBD5E1
- **slate-400**: #94A3B8
- **slate-500**: #64748B
- **slate-600**: #475569
- **slate-700**: #334155
- **slate-800**: #1E293B
- **slate-900**: #0F172A (darkest, primary)

#### Semantic Colors

- **blue-600**: #3B82F6 (primary accent)
- **green-600**: #10B981 (success)
- **amber-600**: #F59E0B (warning)
- **red-600**: #EF4444 (danger)
- **purple-600**: #A855F7 (processing)

### Typography

#### Font Family

```
Font Stack: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

#### Font Sizes

```
xs:    12px (0.75rem)
sm:    14px (0.875rem)
base:  16px (1rem)
lg:    18px (1.125rem)
xl:    20px (1.25rem)
2xl:   24px (1.5rem)
3xl:   30px (1.875rem)
```

#### Font Weights

```
normal:     400
medium:     500
semibold:   600
bold:       700
```

### Spacing Scale

```
0:    0px
1:    4px
2:    8px
3:    12px
4:    16px
6:    24px
8:    32px
```

---

## 🧩 Component Patterns

### Buttons

#### Primary Button (Call-to-Action)

```html
<button
  class="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium px-6 py-2 rounded-lg transition"
>
  Primary Action
</button>
```

#### Secondary Button

```html
<button
  class="bg-slate-100 hover:bg-slate-200 text-slate-900 font-medium px-6 py-2 rounded-lg transition"
>
  Secondary Action
</button>
```

#### Danger Button

```html
<button
  class="bg-red-600 hover:bg-red-700 text-white font-medium px-6 py-2 rounded-lg transition"
>
  Delete or Logout
</button>
```

#### Icon Button

```html
<button class="p-2 hover:bg-slate-100 rounded-lg transition">
  <Icon class="w-5 h-5" />
</button>
```

---

### Input Fields

#### Text Input

```html
<input
  type="text"
  class="w-full px-4 py-2 border border-slate-300 rounded-lg 
         focus:ring-2 focus:ring-blue-500 focus:border-transparent 
         outline-none transition"
  placeholder="Enter text..."
/>
```

#### Input with Icon

```html
<div class="relative">
  <Icon class="absolute left-3 top-3 w-5 h-5 text-slate-400" />
  <input
    type="email"
    class="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg..."
  />
</div>
```

#### Input with Error

```html
<input
  class="w-full px-4 py-2 border border-red-500 rounded-lg 
         focus:ring-2 focus:ring-red-500 focus:border-transparent..."
/>
<p class="text-red-500 text-xs mt-1">Error message</p>
```

#### Select Dropdown

```html
<select
  class="w-full px-4 py-2 border border-slate-300 rounded-lg 
              focus:ring-2 focus:ring-blue-500 outline-none"
>
  <option>Option 1</option>
  <option>Option 2</option>
</select>
```

---

### Badges & Labels

#### Status Badges

```html
<!-- Green - Success -->
<span
  class="px-3 py-1 rounded-full text-xs font-semibold 
           bg-green-100 text-green-800"
>
  Approved
</span>

<!-- Blue - Info -->
<span
  class="px-3 py-1 rounded-full text-xs font-semibold 
           bg-blue-100 text-blue-800"
>
  Uploaded
</span>

<!-- Yellow - Warning -->
<span
  class="px-3 py-1 rounded-full text-xs font-semibold 
           bg-yellow-100 text-yellow-800"
>
  Pending Review
</span>

<!-- Red - Danger -->
<span
  class="px-3 py-1 rounded-full text-xs font-semibold 
           bg-red-100 text-red-800"
>
  Rejected
</span>
```

#### Risk Score Badges

```html
<!-- Low Risk (0-40%) -->
<span
  class="px-3 py-1 rounded-full text-xs font-semibold 
           bg-green-100 text-green-800"
>
  12%
</span>

<!-- Medium Risk (40-70%) -->
<span
  class="px-3 py-1 rounded-full text-xs font-semibold 
           bg-yellow-100 text-yellow-800"
>
  55%
</span>

<!-- High Risk (70%+) -->
<span
  class="px-3 py-1 rounded-full text-xs font-semibold 
           bg-red-100 text-red-800"
>
  85%
</span>
```

---

### Cards

#### Standard Card

```html
<div class="bg-white rounded-lg shadow border border-slate-200 p-6">
  <h3 class="text-lg font-semibold text-slate-900 mb-4">Card Title</h3>
  <p class="text-slate-600">Card content</p>
</div>
```

#### Stat Card

```html
<div class="bg-white rounded-lg shadow border border-slate-200 p-6">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-slate-600 text-sm font-medium">Stat Label</p>
      <p class="text-3xl font-bold text-slate-900 mt-2">24</p>
    </div>
    <div
      class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center"
    >
      <Icon class="w-6 h-6 text-blue-600" />
    </div>
  </div>
</div>
```

#### Info Card (Blue)

```html
<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
  <h4 class="font-semibold text-blue-900 mb-2">Info Title</h4>
  <p class="text-sm text-blue-800">Information content</p>
</div>
```

#### Warning Card (Yellow)

```html
<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
  <h4 class="font-semibold text-yellow-900 mb-2">Warning Title</h4>
  <p class="text-sm text-yellow-800">Warning content</p>
</div>
```

---

### Lists & Tables

#### Table Header

```html
<thead class="bg-slate-50 border-b border-slate-200">
  <tr>
    <th
      class="px-6 py-3 text-left text-xs font-semibold 
               text-slate-700 uppercase"
    >
      Column 1
    </th>
  </tr>
</thead>
```

#### Table Row

```html
<tr class="hover:bg-slate-50 transition border-b border-slate-200">
  <td class="px-6 py-4 text-slate-900">Content</td>
</tr>
```

#### List Item

```html
<div class="flex items-center gap-3 px-4 py-3">
  <Icon class="w-5 h-5 text-slate-400" />
  <span class="text-slate-700">List item</span>
</div>
```

---

### Forms

#### Form Group

```html
<div>
  <label class="block text-sm font-medium text-slate-700 mb-2">
    Label Text *
  </label>
  <input type="text" class="w-full px-4 py-2 border..." />
  {error &&
  <p class="text-red-500 text-xs mt-1">{error}</p>
  }
</div>
```

#### Form Submit

```html
<form onSubmit="{handleSubmit}" class="space-y-6">
  {/* Form fields */}

  <button type="submit" disabled="{loading}" class="w-full ...">
    {loading ? 'Processing...' : 'Submit'}
  </button>
</form>
```

---

### Modals & Dialogs

#### Modal Structure

```html
<div
  class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
>
  <div class="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
    <h2 class="text-xl font-bold text-slate-900 mb-4">Modal Title</h2>
    <p class="text-slate-600 mb-6">Modal content</p>

    <div class="flex gap-3">
      <button class="flex-1 bg-slate-100 hover:bg-slate-200...">Cancel</button>
      <button class="flex-1 bg-blue-600 hover:bg-blue-700...">Confirm</button>
    </div>
  </div>
</div>
```

---

### Navigation

#### Sidebar Navigation Item

```html
<!-- Inactive -->
<a
  href="/dashboard/contracts"
  class="flex items-center gap-3 px-4 py-3 rounded-lg 
          text-slate-400 hover:bg-slate-800 hover:text-white transition"
>
  <Icon class="w-5 h-5" />
  <span>Menu Item</span>
</a>

<!-- Active -->
<a
  href="/dashboard"
  class="flex items-center gap-3 px-4 py-3 rounded-lg 
          bg-blue-600 text-white"
>
  <Icon class="w-5 h-5" />
  <span>Current Page</span>
</a>
```

#### Top Navigation Tab

```html
<!-- Inactive -->
<button
  class="px-6 py-4 font-medium border-b-2 border-transparent 
              text-slate-600 hover:text-slate-900 transition"
>
  Tab 1
</button>

<!-- Active -->
<button
  class="px-6 py-4 font-medium border-b-2 border-blue-600 
              text-blue-600"
>
  Tab 2
</button>
```

---

### Loading States

#### Spinner

```html
<div
  class="w-8 h-8 border-4 border-blue-200 border-t-blue-600 
           rounded-full animate-spin"
></div>
```

#### Loading Text

```html
<p class="text-slate-600">Loading...</p>
```

#### Skeleton Loader (Basic)

```html
<div class="animate-pulse bg-slate-200 h-4 rounded w-3/4"></div>
```

---

### Empty States

#### No Data

```html
<div class="text-center py-8">
  <Icon class="w-12 h-12 text-slate-300 mx-auto mb-3" />
  <p class="text-slate-600">No data found</p>
</div>
```

---

## 🎭 State Examples

### Button States

```
Normal:    blue-600 text-white
Hover:     blue-700
Active:    blue-800
Disabled:  blue-400 cursor-not-allowed
```

### Input States

```
Normal:      border-slate-300 text-slate-900
Focus:       ring-2 ring-blue-500 border-transparent
Error:       border-red-500 ring-2 ring-red-500
Disabled:    bg-slate-50 text-slate-600 cursor-not-allowed
Readonly:    bg-slate-50 text-slate-600 cursor-not-allowed
```

---

## 📐 Common Layout Patterns

### Two-Column Layout

```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
  <div>Column 1</div>
  <div>Column 2</div>
</div>
```

### Three-Column Layout

```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>
```

### Four-Column Stats

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <!-- Stat cards -->
</div>
```

### Sidebar + Content

```html
<div class="flex h-screen">
  <aside class="w-64 bg-slate-900">Sidebar</aside>
  <main class="flex-1 overflow-auto">Content</main>
</div>
```

---

## 🎨 Theme Customization

### In `tailwind.config.ts`

```typescript
theme: {
  extend: {
    colors: {
      'primary': '#0F172A',
      'primary-light': '#1E293B',
      'accent': '#3B82F6',
      'accent-dark': '#1D4ED8',
    },
  },
}
```

---

## ✨ Special Effects

### Hover Transition

```html
<div class="hover:bg-slate-100 transition">Content</div>
```

### Smooth Scroll

```css
html {
  scroll-behavior: smooth;
}
```

### Custom Scrollbar

```css
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-thumb {
  @apply bg-slate-400 rounded;
}
```

---

## 🚀 Usage Tips

1. **Always use semantic HTML** (button, input, form, etc.)
2. **Use Tailwind classes** for styling (no CSS files needed)
3. **Keep component props minimal** (use defaults)
4. **Test responsive breakpoints** (mobile, tablet, desktop)
5. **Ensure accessible colors** (sufficient contrast)
6. **Use consistent spacing** (multiples of 4px)
7. **Add loading states** for all async operations
8. **Show error messages** in a consistent way

---

## 📖 More Resources

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev)
- [Next.js Documentation](https://nextjs.org/docs)
