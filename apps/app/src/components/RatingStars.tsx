import { Text, View } from 'virtual:taro/components'

type RatingStarsProps = {
  value: number
  size?: 'sm' | 'lg'
  disabled?: boolean
  onChange?: (score: number) => void
}

const SCORES = [1, 2, 3, 4, 5]

export function RatingStars({ value, size = 'lg', disabled, onChange }: RatingStarsProps) {
  return (
    <View className={`rw-stars rw-stars--${size}`}>
      {SCORES.map((score) => (
        <Text
          key={score}
          className={`rw-star ${score <= value ? 'rw-star--on' : ''} ${
            disabled ? 'rw-star--disabled' : ''
          }`}
          onClick={() => {
            if (!disabled) onChange?.(score)
          }}
        >
          {score <= value ? '★' : '☆'}
        </Text>
      ))}
    </View>
  )
}
