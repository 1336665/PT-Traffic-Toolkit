<template>
  <span class="counter-animate tabular-nums" :class="{ 'number-pop': popping }">
    {{ displayValue }}
  </span>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'

const props = defineProps({
  value: {
    type: [Number, String],
    default: 0
  },
  duration: {
    type: Number,
    default: 500
  },
  decimals: {
    type: Number,
    default: 0
  },
  prefix: {
    type: String,
    default: ''
  },
  suffix: {
    type: String,
    default: ''
  },
  separator: {
    type: String,
    default: ','
  },
  easing: {
    type: String,
    default: 'easeOutQuart'
  }
})

const displayNumber = ref(0)
const popping = ref(false)
let animationFrame = null
let startTime = null
let startValue = 0

const easingFunctions = {
  linear: t => t,
  easeOutQuart: t => 1 - Math.pow(1 - t, 4),
  easeOutExpo: t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t),
  easeOutCubic: t => 1 - Math.pow(1 - t, 3),
  easeInOutCubic: t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

const formatNumber = (num) => {
  const fixed = Number(num).toFixed(props.decimals)
  const [integer, decimal] = fixed.split('.')
  const formattedInteger = integer.replace(/\B(?=(\d{3})+(?!\d))/g, props.separator)
  return decimal ? `${formattedInteger}.${decimal}` : formattedInteger
}

const displayValue = computed(() => {
  return `${props.prefix}${formatNumber(displayNumber.value)}${props.suffix}`
})

const animate = (timestamp) => {
  if (!startTime) startTime = timestamp
  const elapsed = timestamp - startTime
  const progress = Math.min(elapsed / props.duration, 1)
  const easedProgress = easingFunctions[props.easing](progress)

  const targetValue = Number(props.value) || 0
  displayNumber.value = startValue + (targetValue - startValue) * easedProgress

  if (progress < 1) {
    animationFrame = requestAnimationFrame(animate)
  } else {
    displayNumber.value = targetValue
    // Trigger pop animation on value change
    popping.value = true
    setTimeout(() => {
      popping.value = false
    }, 300)
  }
}

const startAnimation = () => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
  }
  startValue = displayNumber.value
  startTime = null
  animationFrame = requestAnimationFrame(animate)
}

watch(() => props.value, (newVal, oldVal) => {
  if (newVal !== oldVal) {
    startAnimation()
  }
})

onMounted(() => {
  displayNumber.value = Number(props.value) || 0
})
</script>

<style scoped>
.counter-animate {
  display: inline-block;
  transition: color 0.3s ease;
}

@keyframes number-pop {
  0% { opacity: 0.7; }
  50% { opacity: 1; }
  100% { opacity: 1; }
}

.number-pop {
  animation: number-pop 0.3s ease;
}
</style>
